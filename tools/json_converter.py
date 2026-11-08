from runner import run_benchmark as rb
from pathlib import Path
import json


# convert .md task list to JSON
def md_to_json(md_path, json_path=None):
    tasks = rb.parse_md(md_path)
    json_path = Path(json_path) if json_path else Path(md_path)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(tasks, f, indent=4, ensure_ascii=False)
    return json_path