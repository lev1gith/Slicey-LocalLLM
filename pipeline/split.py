from pathlib import Path
import re
import random
import json
from datetime import date
import sys

CHECKS_DIR = Path(__file__).resolve().parent.parent / "checks"
CHECK_MANAGER = "checkManager.py"
CHECK_DEF = re.compile(r"^def check_(\d+)\(", re.M)
SEED = 42
SPLITS_FILE = Path(__file__).resolve().parent.parent /"skills" / "splits.json"


def main():
    # once the frontier model has seen the train chats the split must not change
    # prevent file from being overwritten unless user explicitly asks
    if SPLITS_FILE.exists() and "--force" not in sys.argv:
        sys.exit(f"{SPLITS_FILE} already exists, use --force to overwrite")

    rng = random.Random(SEED)
    categories = get_categories()
    groups = group_by_category(categories)

    train, val, test = [], [], []
    for category in sorted(groups):
        tr, va, te = split_ids(groups[category], rng)
        train.extend(tr)
        val.extend(va)
        test.extend(te)
    print(len(train), len(val), len(test))

    data = {
        "seed": SEED,
        "created": date.today().isoformat(),
        "categories": categories,
        "train": sorted(train),
        "val": sorted(val),
        "test": sorted(test)
    }
    SPLITS_FILE.parent.mkdir(parents=True, exist_ok=True)
    SPLITS_FILE.write_text(json.dumps(data, indent=2))

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

    validation = sor_ids[:n_val]
    test = sor_ids[n_val:n_val + n_test]
    train = sor_ids[n_val + n_test:]

    return train, validation, test

if __name__ == "__main__":
    main()
