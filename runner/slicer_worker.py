import json
import os
import slicer

# task

# start run with empty scene
slicer.mrmlScene.Clear(0)

# initialize slicey and get its logic object
slicer.util.selectModule("Slicey")
slicer.app.processEvents()
widget = slicer.modules.slicey.widgetRepresentation().self()
logic = widget.logic

# Task
logic.sendUserMessage("Test, reply with test success if you get this prompt")

