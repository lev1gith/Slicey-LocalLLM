import json
import os
from pathlib import Path
import requests

Slicer = "/Applications/3D Slicer 5.13.0 2026-10-30.app/Contents/MacOS/SlicerApp-real"
RUNNER_DIR = Path(__file__).resolve().parent
Worker = RUNNER_DIR / "slicer_worker.py"


def main(model, input_format, path):
    if input_format == "json":
        tasks = load_json_tasks(path)
    elif input_format == "md":
        tasks = parse_md(path)
    else:
        raise ValueError("Unsupported format")

    for task in tasks:
        print(f"{task['id']}: {task['prompt']}")

        # store task details in JSON strings in an environment variable
        # worker converts it back to a dictionary(can't pass dict only string
        # in env varible)
        # body of POST
        code = (
            "import os, runpy\n"
            f"os.environ['SLICER_BENCH_TASK_JSON'] = {json.dumps(task)!r}\n"
            f"os.environ['SLICER_BENCH_MODEL'] = {model!r}\n"
            f"runpy.run_path({str(Worker)!r}, run_name='__main__')\n"
        )
        try:
            response = requests.post(
                "http://localhost:2016/slicer/exec",
                data=code,
                timeout=300,
            )
            response.raise_for_status()
            print(response.text)
        except requests.exceptions.RequestException as e:
            print(e)


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
    main(model="qwen3-5-4b", input_format="md", path="tasks/task_prompts.md")
