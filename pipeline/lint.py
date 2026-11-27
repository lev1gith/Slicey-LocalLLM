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
    for check in (check_sources, check_task_ids, check_file_names):
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

# absolute paths from this machine (or any user's home)
ABS_PATH = re.compile(r"/(?:Users|home)/\S*")

# names of the benchmark's test files and folders, lowercased
# (outputs/ is written by the runs, README.md and hidden files like .DS_Store aren't test data)
def test_file_names():
    names = set()
    for p in TEST_FILES.rglob("*"):
        rel = p.relative_to(TEST_FILES)
        if rel.parts[0] == "outputs" or p.name == "README.md" or p.name.startswith("."):
            continue
        names.add(p.name.lower())
    return names

# check that the skill doesn't name the test files or contain absolute paths
def check_file_names(skill):
    text = skill_text(skill).lower()
    problems = []
    for name in sorted(test_file_names()):
        if re.search(r"\b" + re.escape(name) + r"\b", text):
            problems.append(f"mentions test file: {name}")
    for m in ABS_PATH.finditer(skill_text(skill)):
        problems.append(f"contains absolute path: {m.group()}")
    return problems
