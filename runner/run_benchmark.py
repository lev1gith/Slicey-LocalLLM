import json
import os
import subprocess
from pathlib import Path

Slicer = "/Applications/Slicer.app/Contents/MacOS/Slicer"
Worker = Path("slicer_worker.py").resolve()


def main(path="tasks/tasks.json"):
    tasks = load_tasks(path)
        

def load_tasks(path):
    with open(path) as task_json:
        data = json.load(task_json)
        print(data)
    
main()