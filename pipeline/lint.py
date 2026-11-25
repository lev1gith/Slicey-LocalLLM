import json
import re
from pathlib import Path
from split import SPLITS_FILE

TEST_FILES = Path(__file__).resolve().parent.parent / "checks"/ "test_files"


# decides if skill is general enough
# takes one skill dict and returns a list of problems
# empty list -> skill accepted

def check_sources(skill):
    pass

def lint_skill(skill):
    problems = []
    for check in (check_sources(skill)):
        problems.extend(check(skill))
    return problems
