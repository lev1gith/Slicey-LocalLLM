import runpy
from pathlib import Path
import slicer

CHECKS_DIR = Path(__file__).resolve.parent()
CHECK_FILES = ["checkload.py"] # checker files

DATA_CLASSES = ["vtkMRMLScalarVolumeNode", "vtkMRMLSegmentationNode",
                "vtkMRMLModelNode", "vtkMRMLMarkupsNode"]


class CheckContext:
    def __init__(self):
        self.failures = []

    def expect(self, cond, msg):
        if not cond:
            self.failures.append(msg)
        return cond

    def one_node(self, cls, name):
        nodes = [n for n in slicer.util.getNodesByClass(cls) if n.GetName() == name]
        if len(nodes) != 1:
            self.failures.append(f"expected 1 {cls} named '{name}', found {len(nodes)}")
            return None
        return nodes[0]

    def count_data_nodes(self):
        return sum(len(slicer.util.getNodesByClass(c)) for c in DATA_CLASSES)


def load_checks():
    checks = {}
    for name in CHECK_FILES:
        for task_id, fn in runpy.run_path(str(CHECKS_DIR / name))["CHECKS"].items():
            if task_id in checks:
                raise ValueError(f"task {task_id} checked twice ({name})")
            checks[task_id] = fn
    return checks


def run_check(task_id):
    fn = load_checks().get(task_id)
    if fn is None:
        return {"passed": None, "failures": ["no check for this task"]}
    ctx = CheckContext()
    fn(ctx)
    return {"passed": not ctx.failures, "failures": ctx.failures}
