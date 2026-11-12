import json
import os
import slicer
import qt
import time
from pathlib import Path
import runpy
import shutil

def main():
    # load env variables
    task = json.loads(os.environ["SLICER_BENCH_TASK_JSON"])
    model_name = os.environ["SLICER_BENCH_MODEL"]
    CHECK_MANAGER = Path(__file__).resolve().parent.parent / "checks" / "checkManager.py"

    # start run with empty scene
    # initialize slicey and get its logic object
    slicer.mrmlScene.Clear(0)
    # empty outputs so files from earlier can't pass the checks
    outputs = Path("/Users/leventel/Desktop/personalCode/slicey_proj/test_files/outputs")
    outputs.mkdir(parents=True, exist_ok=True)
    for p in outputs.iterdir():
        shutil.rmtree(p) if p.is_dir() else p.unlink()
    slicer.util.selectModule("Slicey")
    slicer.app.processEvents()

    widget = slicer.modules.slicey.widgetRepresentation().self()
    combo = widget.ui.modelComboBox

    if combo.findText(model_name) < 0:
        raise ValueError(f"Model not listed in slicey: {model_name}")

    combo.setCurrentText(model_name)
    logic = widget.logic
    logic.resetConversation()

    # create event loop so this script can wait while slicey works
    # slices sends the model request and processes the response async
    timeout = 150
    loop = qt.QEventLoop()
    finished = {"value": False, "timed_out": False, "errors": []}

    timer = qt.QTimer()
    timer.setSingleShot(True)

    def on_timeout():
        finished["timed_out"] = True
        print(f"Task: {task['id']} timed out")
        loop.quit()

    timer.timeout.connect(on_timeout)

    # keep slicey's existing event handler(which updates its UI), then
    # add a seperate handler to detect when the task is finished
    prev_handler = logic.onEvent

    def on_event(event, payload):
        if prev_handler:
            prev_handler(event, payload)
        if event == "error":
            finished["errors"].append(str(payload))
        # slicey emits "turn_finished" when it completed the request
        # and any tool calls for this turn
        if event == "turn_finished":
            finished["value"] = True
            loop.quit()

    start = time.perf_counter()
    timer.start(timeout * 1000)
    try:
        logic.onEvent = on_event
        if logic._busy:  # make sure not to have task leaks
            raise RuntimeError("Slicey still busy from previous task")
        qt.QTimer.singleShot(0, lambda: logic.sendUserMessage(task["prompt"]))
        # schedule the prompt after the event loop starts so it can receive
        # slicey's completion event while the request is running
        loop.exec_()  # wait here until slicey finishes
    finally:
        logic.onEvent = prev_handler  # restore slicey's original event handler
        timer.stop()
    llm_s = time.perf_counter() - start  # time from sending prompt until loop ends

    if finished["timed_out"]:
        logic.cancel()
        deadline = time.perf_counter() + 20
        while logic._busy and time.perf_counter() < deadline:
            slicer.app.processEvents()
            time.sleep(0.05)
        result = {"outcome": "timeout", "reason": f"no turn finished within {timeout} s", "cancel_clean": not logic._busy, 
                  "passed": False}
    elif finished["errors"]:
        result = {"outcome": "slicey_error", "reason": finished["errors"][-1], "passed": False}
    else:
        result = {"outcome": "finished", "reason": "turn finished"}
        try:
            run_check = runpy.run_path(str(CHECK_MANAGER))["run_check"]
            result.update(run_check(task["id"]))  # sets "passed"
        except Exception as e:
            result["passed"] = None
            result["checker_error"] = repr(e)
    result["llm_s"] = round(llm_s, 2)
    if finished["errors"]:
        result["errors"] = finished["errors"]

    return result


def run():
    # RESULT is sent back to the runner via __execResult, so turn worker
    # exceptions (e.g. model not listed) into a record instead of crashing
    try:
        return main()
    except Exception as e:
        return {"outcome": "worker_error", "reason": repr(e), "passed": None}


RESULT = run()
