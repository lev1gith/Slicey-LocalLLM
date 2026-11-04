import json
import os
import slicer


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
    logic.sendUserMessage(task["prompt"]) # run prompt

    # check result

main()