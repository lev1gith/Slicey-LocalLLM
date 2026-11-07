import json
import os
import subprocess
from pathlib import Path
import requests

Slicer = "/Applications/3D Slicer 5.13.0 2026-10-30.app/Contents/MacOS/SlicerApp-real"
RUNNER_DIR = Path(__file__).resolve().parent
Worker = RUNNER_DIR / "slicer_worker.py"


def main(model, path="tasks/tasks.json"):
    tasks = load_tasks(path)
    for task in tasks:
        print(f"{task['id']}: {task['prompt']}")

        # store task details in JSON strings in an environment variable
        # worker converts it back to a dictionary(can't pass dict only string
        # in env varible)
        env = os.environ.copy()
        env["SLICER_BENCH_TASK_JSON"] = json.dumps(task)
        env["SLICER_BENCH_MODEL"] = model

        # body of POST
        code = (
            "import os, runpy\n"
            f"os.environ['SLICER_BENCH_TASK_JSON'] = {json.dumps(task)!r}\n"
            f"os.environ['SLICER_BENCH_MODEL'] = {model!r}\n"
            f"runpy.run_path({str(Worker)!r}, run_name='__main__')\n"
        )

        response = requests.post(
            "http://localhost:2016/slicer/exec",
            data=code,
            timeout=300,
        )
        response.raise_for_status()
        print(response.text)

def load_tasks(path):
    with open(path, encoding="utf-8") as task_json:
        return json.load(task_json)


main(model="qwen3-5-4b")
