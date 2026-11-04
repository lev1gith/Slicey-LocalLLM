import json
import os
import slicer
import qt

def main():
    # task
    task = json.loads(os.environ["SLICER_BENCH_TASK_JSON"])
    model_name = os.environ["SLICER_BENCH_MODEL"]


    # start run with empty scene
    # initialize slicey and get its logic object
    slicer.mrmlScene.Clear(0)
    slicer.util.selectModule("Slicey")
    slicer.app.processEvents()

    widget = slicer.modules.slicey.widgetRepresentation().self()
    combo = widget.ui.modelComboBox

    if combo.findText(model_name) < 0:
        raise ValueError(f"Model not listed in slicey: {model_name}")

    combo.setCurrentText(model_name)
    logic = widget.logic

    # create event loop so this script can wait while slicey works
    # slices sends the model request and processes the response async
    loop = qt.QEventLoop()
    finished = {"value": False}

    # keep slicey's existing event handler(which updates its UI), then
    # add a seperate handler to detect when the task is finished
    prev_handler = logic.onEvent

    def on_event(event, payload):
        if prev_handler:
            prev_handler(event, payload)

        # slicey emits "turn_finishes when it completed the request"
        # and any tool calls for this turn
        if event == "turn_finished":
            finished["value"] = True
            loop.quit()

    logic.onEvent = on_event

    # schedule the prompt after the event loop starts so it can receive
    # slicey's completion event while the request is running
    qt.QTimer.singleShot(0, lambda: logic.sendUserMessage(task["prompt"]))
    loop.exec_()  # wait here until slicey finishes
    logic.onEvent = prev_handler  # restore slicey's original event handler

    # check result

main()