import json
import re
from pathlib import Path
from split import SPLITS_FILE

TEST_FILES = Path(__file__).resolve().parent.parent / "checks"/ "test_files"


# decides if skill is general enough
# takes one skill dict and returns a list of problems
# empty list -> skill accepted

# check if every id in sources are in the training split
def check_sources(skill):
    text = SPLITS_FILE.read_text(encoding="utf-8")
    splits = json.loads(text)
    train = set(splits["train"])

    problems = []
    if not skill["sources"]:
        problems.append("skill has no sources")
    for task_id in skill["sources"]:
        if task_id not in train:
            problems.append(f"source {task_id} is not a train task")
    return problems

def lint_skill(skill):
    problems = []
    for check in (check_sources, check_task_ids):
        problems.extend(check(skill))
    return problems

# helper function: join name, description and body to 1 string
def skill_text(skill):
    skill_parts = [skill["name"], skill["description"], skill["body"]]
    text = "\n".join(skill_parts)
    return text

# "task 34", "Task_07", "task34", "check_05", "check 12"; \b so "subtask" doesn't match
TASK_ID = re.compile(r"\b(?:task|check)[\s_]?\d{1,2}\b", re.IGNORECASE)

# check that the skill doesn't name a specific benchmark task
def check_task_ids(skill):
    text = skill_text(skill)
    problems = []
    for m in TASK_ID.finditer(text):
        problems.append(f"mentions task id: {m.group()}")
    return problems
