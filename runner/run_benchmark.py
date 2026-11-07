import json
import os
import subprocess
from pathlib import Path

Slicer = "/Applications/Slicer.app/Contents/MacOS/Slicer"
Worker = Path("slicer_worker.py").resolve()


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

        try:
            result = subprocess.run(
                [
                    Slicer,
                    "--no-splash",
                    "--no-main-window",
                    "--python-script",
                    str(Worker),
                ],
                env=env,
                timeout=300,
                check=False,
            )
        except subprocess.TimeoutExpired:
            print(f"Timeout while running {task['id']}")


def load_tasks(path):
    with open(path, encoding="utf-8") as task_json:
        return json.load(task_json)


main(model="qwen3-5-4b")
