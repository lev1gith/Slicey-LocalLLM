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
    for check in (check_sources,):
        problems.extend(check(skill))
    return problems
