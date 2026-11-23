from pathlib import Path
import re

CHECKS_DIR = Path(__file__).resolve().parent.parent / "checks"
CHECK_MANAGER = "checkManager.py"
CHECK_DEF = re.compile(r"^def check_(\d+)\(", re.M)

# gets the category of each task, eg 01:'Load', 24:'Measure'...
def get_categories():
    categories = {}
    for path in sorted(CHECKS_DIR.glob("check*.py")):
        if (path.name == CHECK_MANAGER):
            continue
        category = path.stem.removeprefix("check").lower()
        for task_id in CHECK_DEF.findall(path.read_text()):
            categories[task_id] = category
    return categories
