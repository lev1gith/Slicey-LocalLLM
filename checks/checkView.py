import slicer

# View and display checks (tasks 26-33).
# Loaded inputs are found by their source file, whatever their name.
# View state (layout, slice orientation/offset) is not part of the scene's
# data, so the worker resets it before every task; otherwise a task could
# pass on what an earlier task left behind.


# --- helpers -----------------------------------------------------------------

def close(a, b, tol=0.01):
    return all(abs(x - y) <= tol for x, y in zip(a, b))


def by_layout_name(cls, name):
    # slice and composite nodes for "Red", "Yellow", "Green"
    for n in slicer.util.getNodesByClass(cls):
        if n.GetLayoutName() == name:
            return n
    return None


def check_background(ctx, view, volume):
    composite = by_layout_name("vtkMRMLSliceCompositeNode", view)
    if not ctx.expect(composite is not None, f"no {view} slice view"):
        return False
    return ctx.expect(composite.GetBackgroundVolumeID() == volume.GetID(),
                      f"{view} view background is {composite.GetBackgroundVolumeID()}, "
                      f"expected '{volume.GetName()}' ({volume.GetID()})")


def slice_offset(slice_node):
    # offset of the slice plane along its normal, as the slice slider shows it
    m = slice_node.GetSliceToRAS()
    normal = [m.GetElement(i, 2) for i in range(3)]
    origin = [m.GetElement(i, 3) for i in range(3)]
    return sum(n * o for n, o in zip(normal, origin))


def benchmark_ct(ctx):
    return ctx.node_from_file("vtkMRMLScalarVolumeNode", "benchmark_ct.nrrd")


# --- 26-30: layout and slice views -------------------------------------------

# 26 — Set the four-up layout
def check_26(ctx):
    layout = slicer.app.layoutManager().layout
    ctx.expect(layout == slicer.vtkMRMLLayoutNode.SlicerLayoutFourUpView,
               f"layout is {layout}, expected SlicerLayoutFourUpView "
               f"({slicer.vtkMRMLLayoutNode.SlicerLayoutFourUpView})")


# 27 — Show a volume in slice views
def check_27(ctx):
    ct = benchmark_ct(ctx)
    if ct is None:
        return
    for view in ("Red", "Yellow", "Green"):
        check_background(ctx, view, ct)


# 28 — Set slice orientation
def check_28(ctx):
    ct = benchmark_ct(ctx)
    if ct is None:
        return
    check_background(ctx, "Red", ct)
    red = by_layout_name("vtkMRMLSliceNode", "Red")
    ctx.expect(red.GetOrientation() == "Sagittal",
               f"Red view orientation is {red.GetOrientation()}, expected Sagittal")


# 29 — Set slice position
def check_29(ctx):
    ct = benchmark_ct(ctx)
    if ct is None:
        return
    check_background(ctx, "Red", ct)
    offset = slice_offset(by_layout_name("vtkMRMLSliceNode", "Red"))
    ctx.expect(abs(offset - 5) <= 0.01, f"Red view offset {offset:.3f} mm, expected 5")


# 30 — Set window and level
def check_30(ctx):
    ct = benchmark_ct(ctx)
    if ct is None:
        return
    display = ct.GetDisplayNode()
    if not ctx.expect(display is not None, "volume has no display node"):
        return
    ctx.expect(abs(display.GetWindow() - 1600) <= 0.5,
               f"window {display.GetWindow():.1f}, expected 1600")
    ctx.expect(abs(display.GetLevel() - 300) <= 0.5,
               f"level {display.GetLevel():.1f}, expected 300")


# --- 31-33: 3D display -------------------------------------------------------

# 31 — Show a segmentation in 3D
def check_31(ctx):
    seg = ctx.node_from_file("vtkMRMLSegmentationNode", "islands.seg.nrrd")
    if seg is None:
        return
    segmentation = seg.GetSegmentation()
    segment_id = segmentation.GetSegmentIdBySegmentName("TumorMask")
    if not ctx.expect(segment_id, "no segment named 'TumorMask'"):
        return
    ctx.expect(segmentation.ContainsRepresentation("Closed surface"),
               "segmentation has no closed-surface representation")
    display = seg.GetDisplayNode()
    if not ctx.expect(display is not None, "segmentation has no display node"):
        return
    # all three switches have to be on for the segment to appear in 3D
    ctx.expect(display.GetVisibility(), "segmentation is hidden")
    ctx.expect(display.GetVisibility3D(), "segmentation is hidden in 3D")
    ctx.expect(display.GetSegmentVisibility(segment_id), "TumorMask segment is hidden")


# 32 — Set model display properties
def check_32(ctx):
    model = ctx.node_from_file("vtkMRMLModelNode", "sphere_model.stl")
    if model is None:
        return
    display = model.GetDisplayNode()
    if not ctx.expect(display is not None, "model has no display node"):
        return
    color = display.GetColor()
    ctx.expect(close(color, (0.1, 0.4, 0.9)),
               f"color {tuple(round(c, 3) for c in color)}, expected (0.1, 0.4, 0.9)")
    ctx.expect(abs(display.GetOpacity() - 0.65) <= 0.01,
               f"opacity {display.GetOpacity():.3f}, expected 0.65")


# 33 — Enable volume rendering
def check_33(ctx):
    ct = benchmark_ct(ctx)
    if ct is None:
        return
    logic = slicer.modules.volumerendering.logic()
    display = logic.GetFirstVolumeRenderingDisplayNode(ct)
    if not ctx.expect(display is not None, "no volume rendering for the volume"):
        return
    ctx.expect(display.GetVisibility(), "volume rendering is hidden")
    # an empty view list means "all views"; otherwise the 3D view must be in it
    view_ids = [display.GetNthViewNodeID(i) for i in range(display.GetNumberOfViewNodeIDs())]
    three_d = [v.GetID() for v in slicer.util.getNodesByClass("vtkMRMLViewNode")]
    ctx.expect(not view_ids or any(v in view_ids for v in three_d),
               f"volume rendering not shown in a 3D view (views: {view_ids})")


CHECKS = {
    "26": check_26,
    "27": check_27,
    "28": check_28,
    "29": check_29,
    "30": check_30,
    "31": check_31,
    "32": check_32,
    "33": check_33,
}
