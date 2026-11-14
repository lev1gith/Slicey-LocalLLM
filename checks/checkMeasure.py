import slicer

# Markups and measurement checks (tasks 19-25).
# Created objects are found by the exact name the prompt asks for;
# loaded inputs (24, 25) are found by their source file, whatever their name.

TOL_MM = 0.01  # position tolerance for markups placed at exact coordinates


# --- helpers -----------------------------------------------------------------

def close(a, b, tol=TOL_MM):
    return all(abs(x - y) <= tol for x, y in zip(a, b))


def fmt(p):
    return tuple(round(x, 3) for x in p)


def control_points(markups):
    return [markups.GetNthControlPointPosition(i)
            for i in range(markups.GetNumberOfControlPoints())]


def check_points(ctx, markups, expected):
    # exact number of points, each at its expected position, in this order
    points = control_points(markups)
    if not ctx.expect(len(points) == len(expected),
                      f"expected {len(expected)} points, found {len(points)}"):
        return False
    ok = True
    for i, (p, e) in enumerate(zip(points, expected)):
        ok &= ctx.expect(close(p, e), f"point {i} at {fmt(p)}, expected {e}")
    return ok


def exact_class(ctx, node, cls):
    # getNodesByClass also returns subclasses (e.g. a closed curve is a curve)
    return ctx.expect(node.GetClassName() == cls,
                      f"'{node.GetName()}' is a {node.GetClassName()}, expected {cls}")


def table_numbers(table_node):
    # every cell of the table that reads as a number
    table = table_node.GetTable()
    numbers = []
    for r in range(table.GetNumberOfRows()):
        for c in range(table.GetNumberOfColumns()):
            try:
                numbers.append(float(table.GetValue(r, c).ToString()))
            except ValueError:
                pass
    return numbers


def has_value(numbers, expected, rel=0.02):
    # within 2%, so labelmap vs. surface-based volumes both count
    return any(abs(n - expected) <= rel * abs(expected) for n in numbers)


def tumor_mask_volume(seg):
    # TumorMask volume in mm3 from the segment's own labelmap
    segment_id = seg.GetSegmentation().GetSegmentIdBySegmentName("TumorMask")
    if not segment_id:
        return None, None
    segment = seg.GetSegmentation().GetSegment(segment_id)
    labelmap = slicer.util.arrayFromSegmentInternalBinaryLabelmap(seg, segment_id)
    voxels = int((labelmap == segment.GetLabelValue()).sum())
    sx, sy, sz = segment.GetRepresentation("Binary labelmap").GetSpacing()
    return segment_id, voxels * sx * sy * sz


# --- 19-23: markups at exact coordinates -------------------------------------

# 19 — Place a markup point
def check_19(ctx):
    points = ctx.one_node("vtkMRMLMarkupsFiducialNode", "Target Point")
    if points is None:
        return
    check_points(ctx, points, [(5, 10, 15)])


# 20 — Measure a line between two points
def check_20(ctx):
    line = ctx.one_node("vtkMRMLMarkupsLineNode", "50 mm Test Line")
    if line is None:
        return
    points = control_points(line)
    if not ctx.expect(len(points) == 2, f"expected 2 points, found {len(points)}"):
        return
    # the prompt gives no order for the endpoints, so either way round counts
    a, b = (0, 0, 0), (30, 40, 0)
    p, q = points
    ctx.expect((close(p, a) and close(q, b)) or (close(p, b) and close(q, a)),
               f"endpoints at {fmt(p)} and {fmt(q)}, expected {a} and {b}")
    ctx.expect(abs(line.GetLineLengthWorld() - 50) <= TOL_MM,
               f"line length {line.GetLineLengthWorld():.3f} mm, expected 50")


# 21 — Measure an angle
def check_21(ctx):
    angle = ctx.one_node("vtkMRMLMarkupsAngleNode", "Right Angle Test")
    if angle is None:
        return
    # order matters here: the middle point is the vertex
    if check_points(ctx, angle, [(1, 0, 0), (0, 0, 0), (0, 1, 0)]):
        ctx.expect(abs(angle.GetAngleDegrees() - 90) <= 0.01,
                   f"angle {angle.GetAngleDegrees():.3f}°, expected 90")


# 22 — Create a curve markup
def check_22(ctx):
    curve = ctx.one_node("vtkMRMLMarkupsCurveNode", "Benchmark Curve")
    if curve is None:
        return
    exact_class(ctx, curve, "vtkMRMLMarkupsCurveNode")  # open curve, not closed
    check_points(ctx, curve, [(0, 0, 0), (10, 5, 0), (20, 0, 5), (30, 5, 10)])


# 23 — Create a region of interest
def check_23(ctx):
    roi = ctx.one_node("vtkMRMLMarkupsROINode", "Benchmark ROI")
    if roi is None:
        return
    center = [0.0, 0.0, 0.0]
    roi.GetCenter(center)
    size = roi.GetSize()
    ctx.expect(close(center, (0, 0, 0)), f"center at {fmt(center)}, expected (0, 0, 0)")
    ctx.expect(close(size, (20, 30, 40)), f"size {fmt(size)}, expected (20, 30, 40)")


# --- 24-25: segment measurements saved in tables ----------------------------

# 24 — Compute segment statistics
def check_24(ctx):
    ct = ctx.node_from_file("vtkMRMLScalarVolumeNode", "benchmark_ct.nrrd")
    seg = ctx.node_from_file("vtkMRMLSegmentationNode", "islands.seg.nrrd")
    table = ctx.one_node("vtkMRMLTableNode", "Tumor Statistics")
    if ct is None or seg is None or table is None:
        return

    segment_id, volume_mm3 = tumor_mask_volume(seg)
    if not ctx.expect(segment_id, "no segment named 'TumorMask'"):
        return
    # mean CT intensity inside the segment, on the CT's own voxel grid
    mask = slicer.util.arrayFromSegmentBinaryLabelmap(seg, segment_id, ct)
    mean = float(slicer.util.arrayFromVolume(ct)[mask > 0].mean())

    numbers = table_numbers(table)
    ctx.expect(has_value(numbers, volume_mm3) or has_value(numbers, volume_mm3 / 1000),
               f"table has no TumorMask volume ({volume_mm3:.1f} mm3 / {volume_mm3 / 1000:.4f} cm3)")
    ctx.expect(has_value(numbers, mean),
               f"table has no mean intensity ({mean:.1f})")


# 25 — Measure a segment's volume
def check_25(ctx):
    seg = ctx.node_from_file("vtkMRMLSegmentationNode", "islands.seg.nrrd")
    table = ctx.one_node("vtkMRMLTableNode", "Tumor Volume")
    if seg is None or table is None:
        return

    segment_id, volume_mm3 = tumor_mask_volume(seg)
    if not ctx.expect(segment_id, "no segment named 'TumorMask'"):
        return
    numbers = table_numbers(table)
    ctx.expect(has_value(numbers, volume_mm3) or has_value(numbers, volume_mm3 / 1000),
               f"table has no TumorMask volume ({volume_mm3:.1f} mm3 / {volume_mm3 / 1000:.4f} cm3)")


CHECKS = {
    "19": check_19,
    "20": check_20,
    "21": check_21,
    "22": check_22,
    "23": check_23,
    "24": check_24,
    "25": check_25,
}
