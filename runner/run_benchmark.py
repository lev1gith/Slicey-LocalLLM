import json
from pathlib import Path
import requests
import time
from datetime import datetime

RUNNER_DIR = Path(__file__).resolve().parent
Worker = RUNNER_DIR / "slicer_worker.py"
Result_dir = RUNNER_DIR.parent / "results"
TASKS_DIR = RUNNER_DIR.parent / "tasks"
TEST_FILES = RUNNER_DIR.parent / "checks" / "test_files"
SPLITS_FILE = RUNNER_DIR.parent / "skills" / "splits.json"

def main(model, path, task_ids=None, repeats=1, skills=""):
    path = TASKS_DIR / path
    if path.suffix == ".json":
        tasks = load_json_tasks(path)
    elif path.suffix == ".md":
        tasks = parse_md(path)
    else:
        raise ValueError(f"Unsupported task file: {path.name}")

    if task_ids:
        missing = task_ids - {t["id"] for t in tasks}
        if missing:
            raise ValueError(f"Unknown task ids: {sorted(missing)}")
        tasks = [t for t in tasks if t["id"] in task_ids]

    for task in tasks:
        task["prompt"] = task["prompt"].replace("{TEST_FILES}", str(TEST_FILES))

    run_id, run_dir = new_run_dir(model)
    scenes_dir = run_dir / "outputs" # worker saves each task's scene here as .mrb
    scenes_dir.mkdir(exist_ok=True)
    print(f"Run {run_id} -> {run_dir}", flush=True)

    for repeat in range(1, repeats + 1):
        for task in tasks:
            print(f"{task['id']}: {task['prompt']}")

            # body of POST
            # Slicer's /slicer/exec returns the value of __execResult as JSON
            # (printed output is not returned), so pass the worker's RESULT there
            scene_file = scenes_dir / f"task{task['id']}_rep{repeat}_outp.mrb"
            code = (
                "import os, runpy\n"
                f"os.environ['SLICER_BENCH_TASK_JSON'] = {json.dumps(task)!r}\n"
                f"os.environ['SLICER_BENCH_MODEL'] = {model!r}\n"
                f"os.environ['SLICER_BENCH_SCENE_FILE'] = {str(scene_file)!r}\n"
                f"os.environ['SLICER_BENCH_SKILLS'] = {skills!r}\n"
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
            record["repeat"] = repeat
            record["skills"] = skills
            record["run_id"] = run_id
            record["model"] = model
            record["timestamp"] = datetime.now().isoformat(timespec="seconds")

            print(f"  -> {record['outcome']}: {record.get('reason', '')} ({wall_s}s)", flush=True)
            append_record(run_dir, record)


def append_record(run_dir, record):
    # open, write one line, close: each task is on disk before the next starts
    with open(run_dir / "results.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def new_run_dir(model):
    safe_model = model.replace("/", "_")  # make sure "/" in model name doesn't create subfolder
    run_id = f"{safe_model}_{datetime.now().strftime('%Y-%m-%dT%H-%M-%S')}"
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


def parse_task_ids(spec):
    # "01-08,11" -> {"01", ..., "08", "11"}; keeps zero-padding like "01"
    ids = set()
    for part in spec.split(","):
        part = part.strip()
        if "-" in part:
            start, end = part.split("-")
            width = len(start)
            ids.update(str(i).zfill(width) for i in range(int(start), int(end) + 1))
        elif part:
            ids.add(part)
    return ids


def load_split(name):
    if not SPLITS_FILE.exists():
        raise ValueError("Error, splits file doesn't exist. Run pipeline/split.py to create it")
    tasks = Path.read_text(SPLITS_FILE)
    splits = json.loads(tasks)
    return set(splits[name])

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Run Slicey benchmark tasks")
    p.add_argument("--model", default="qwen3-5-4b", help="model name as shown in Slicey")
    p.add_argument("--file", default="task_prompts.md", help="task file in tasks/")
    p.add_argument("--tasks", help='task ids, e.g. "01-08,11" (default: all)')
    p.add_argument("--split", choices=["train", "val", "test"], help="run only split x from skills/splits.json")
    p.add_argument("--skills", help="folder with the skills to use (default: no skills), eg skills/library")
    p.add_argument("--repeats", type=int, default=1, help="run each task N times")
    args = p.parse_args()
    if args.tasks and args.split:
        p.error("use either --tasks or --split, not both")

    if args.tasks:
        selected_ids = parse_task_ids(args.tasks)
    elif args.split:
        selected_ids = load_split(args.split)
    else:
        selected_ids = None

    selected_skills = ""
    if args.skills:
        folder = Path(args.skills).resolve()
        if (not folder.is_dir()):
            p.error(f"Folder doesn't exist {folder}")
        selected_skills = str(folder)
    main(model=args.model, path=args.file,
         task_ids = selected_ids,
         repeats=args.repeats, skills=selected_skills)
