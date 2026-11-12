import json
import os
from pathlib import Path
import requests
import time
from datetime import datetime

Slicer = "/Applications/3D Slicer 5.13.0 2026-10-30.app/Contents/MacOS/SlicerApp-real"
RUNNER_DIR = Path(__file__).resolve().parent
Worker = RUNNER_DIR / "slicer_worker.py"
Result_dir = RUNNER_DIR.parent / "results"
TASKS_DIR = RUNNER_DIR.parent / "tasks"
TEST_FILES = RUNNER_DIR.parent / "checks" / "test_files"


def main(model, input_format, path):
    path = TASKS_DIR / path  # task files are looked up in tasks/
    if input_format == "json":
        tasks = load_json_tasks(path)
    elif input_format == "md":
        tasks = parse_md(path)
    else:
        raise ValueError("Unsupported format")

    for task in tasks:
        task["prompt"] = task["prompt"].replace("{TEST_FILES}", str(TEST_FILES))

    run_id, run_dir = new_run_dir()
    print(f"Run {run_id} -> {run_dir}", flush=True)

    for task in tasks:
        print(f"{task['id']}: {task['prompt']}")

        # store task details in JSON strings in an environment variable
        # worker converts it back to a dictionary(can't pass dict only string
        # in env varible)
        # body of POST
        # Slicer's /slicer/exec returns the value of __execResult as JSON
        # (printed output is not returned), so pass the worker's RESULT there
        code = (
            "import os, runpy\n"
            f"os.environ['SLICER_BENCH_TASK_JSON'] = {json.dumps(task)!r}\n"
            f"os.environ['SLICER_BENCH_MODEL'] = {model!r}\n"
            f"__execResult = runpy.run_path({str(Worker)!r}, run_name='__main__')['RESULT']\n"
        )
        start = time.perf_counter()
        try:
            response = requests.post(
                "http://localhost:2016/slicer/exec",
                data=code,
                timeout=300,
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            record = {"outcome": "request_error", "reason": str(e)}
        else:
            try:
                record = response.json()
            except ValueError:
                record = {
                    "outcome": "code_error",
                    "reason": "non-JSON response",
                    "raw": response.text[-500:],
                }
            if not isinstance(record, dict) or not record:
                # {} means __execResult was never set by the worker
                record = {
                    "outcome": "code_error",
                    "reason": "worker returned no result",
                    "raw": response.text[-500:],
                }
        wall_s = round(time.perf_counter() - start, 2)
        record["task_id"] = task["id"]
        record["wall_s"] = wall_s
        record["run_id"] = run_id
        record["model"] = model
        record["timestamp"] = datetime.now().isoformat(timespec="seconds")

        print(f"  -> {record['outcome']}: {record.get('reason', '')} ({wall_s}s)", flush=True)
        append_record(run_dir, record)


def append_record(run_dir, record):
    # open, write one line, close: each task is on disk before the next starts
    with open(run_dir / "results.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def new_run_dir():
    run_id = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
    run_dir = Result_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_id, run_dir


def load_json_tasks(path):
    with open(path, encoding="utf-8") as task_json:
        return json.load(task_json)


def parse_md(path):
    text = Path(path).read_text(encoding="utf-8")
    tasks = []
    curr = None

    def flush(task):
        if task is None:
            return
        prompt = "\n".join(task["lines"]).strip()
        if not prompt:
            raise ValueError(f"Task {task['id']} has empty prompt")
        tasks.append({"id": task["id"], "prompt": prompt})

    for line in text.splitlines():
        if line.startswith("### "):
            flush(curr)
            heading = line[4:].strip()
            if " — " not in heading:
                raise ValueError("Bad task heading")
            task_id, _title = heading.split(" — ", maxsplit=1)
            curr = {"id": task_id.strip(), "lines": []}
        elif curr is not None:
            curr["lines"].append(line)
    flush(curr)  # last task

    ids = [t["id"] for t in tasks]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate task ids in markdown file")

    if not tasks:
        raise ValueError(f"No tasks found in {path}")
    return tasks


if __name__ == "__main__":
    main(model="qwen3-5-4b", input_format="md", path="task_prompts.md")
