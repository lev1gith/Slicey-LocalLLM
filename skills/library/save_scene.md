---
description: How to save the scene or a node to a file
category: export
sources: 34, 36
---
Use slicer.util.saveNode(node, path) for a single node, and
slicer.util.saveScene(path) for the whole scene (.mrb). Both return
True on success, so check the return value instead of assuming it worked.
Write outputs only into the writable shared folder.
