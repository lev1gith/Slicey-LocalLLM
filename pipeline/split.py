from pathlib import Path
import re
import random

CHECKS_DIR = Path(__file__).resolve().parent.parent / "checks"
CHECK_MANAGER = "checkManager.py"
CHECK_DEF = re.compile(r"^def check_(\d+)\(", re.M)
seed = 42

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


def group_by_category(categories):
    groups = {}
    for task_id, category in categories.items():
        groups.setdefault(category, []).append(task_id)
    return groups

def split_ids(ids, rng):
    sor_ids = sorted(ids)
    rng.shuffle(sor_ids)
    n = len(sor_ids)
    n_val = max(1, round(0.2 * n))
    n_test = max(1, round(0.2 * n))

    validation = ids[:n_val]
    test = ids[n_val:n_val + n_test]
    train = ids[n_val + n_test]

    return train, validation, test
