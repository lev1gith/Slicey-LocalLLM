import numpy as np
import slicer
import vtk
from vtk.util import numpy_support

# Segmentation checks (tasks 09-18).
# Created segmentations are found by exact name; loaded inputs by source file.
# Masks are compared as sets of voxel centers in world (RAS) coordinates, so
# a segment only matches if it is on the same voxel grid as the expected
# result; a segment that was resampled to another grid fails.
# Expected results are computed from the fixture files, read into a
# throwaway scene so the scene being checked isn't touched.


# --- reading masks -----------------------------------------------------------

def matrix_array(m):
    return np.array([[m.GetElement(i, j) for j in range(4)] for i in range(4)])


def image_voxels(image, label):
    # absolute IJK indices of the voxels equal to label, and the IJK -> RAS
    # matrix; segment labelmaps can share one image, so match the label value
    if image is None:
        return np.zeros((0, 3), int), None
    m = vtk.vtkMatrix4x4()
    image.GetImageToWorldMatrix(m)
    e = image.GetExtent()
    scalars = image.GetPointData().GetScalars()
    if scalars is None or e[1] < e[0] or e[3] < e[2] or e[5] < e[4]:
        return np.zeros((0, 3), int), matrix_array(m)  # empty segment
    dims = image.GetDimensions()
    array = numpy_support.vtk_to_numpy(scalars).reshape(dims[2], dims[1], dims[0])
    ijk = np.argwhere(array == label)[:, ::-1] + [e[0], e[2], e[4]]
    return ijk, matrix_array(m)


def to_world(ijk, M):
    return ijk @ M[:3, :3].T + M[:3, 3]


def to_set(ijk, M):
    # voxel centers in RAS, rounded so the same voxel compares equal
    if M is None or len(ijk) == 0:
        return set()
    return set(map(tuple, np.round(to_world(np.asarray(ijk), M), 2)))


def segment_labelmap(segment):
    name = slicer.vtkSegmentationConverter.GetBinaryLabelmapRepresentationName()
    return image_voxels(segment.GetRepresentation(name), segment.GetLabelValue())


def segment_set(seg, segment_id):
    return to_set(*segment_labelmap(seg.GetSegmentation().GetSegment(segment_id)))


def reference_geometry(segmentation):
    # (IJK -> RAS matrix, extent) the segmentation was set up with, or None.
    # Stored as 16 matrix values then 6 extent values, separated by ';'
    name = slicer.vtkSegmentationConverter.GetReferenceImageGeometryParameterName()
    text = segmentation.GetConversionParameter(name) or ""
    try:
        values = [float(v) for v in text.split(";") if v.strip()]
    except ValueError:
        return None
    if len(values) < 22:
        return None
    return np.array(values[:16]).reshape(4, 4), [int(round(v)) for v in values[16:22]]


# --- fixtures ----------------------------------------------------------------

def read_volume(path, cls="vtkMRMLScalarVolumeNode"):
    scene = slicer.vtkMRMLScene()
    node = scene.AddNewNodeByClass(cls)
    storage = scene.AddNewNodeByClass("vtkMRMLVolumeArchetypeStorageNode")
    storage.SetFileName(path)
    storage.ReadData(node)
    m = vtk.vtkMatrix4x4()
    node.GetIJKToRASMatrix(m)
    return slicer.util.arrayFromVolume(node).copy(), matrix_array(m)


def range_set(volume, lo, hi):
    # voxels of a fixture volume with lo <= value <= hi
    array, M = volume
    return to_set(np.argwhere((array >= lo) & (array <= hi))[:, ::-1], M)


def fixture_tumor(ctx):
    # TumorMask of islands.seg.nrrd: voxel indices, matrix, reference geometry
    scene = slicer.vtkMRMLScene()
    node = scene.AddNewNodeByClass("vtkMRMLSegmentationNode")
    storage = scene.AddNewNodeByClass("vtkMRMLSegmentationStorageNode")
    storage.SetFileName(ctx.path("islands.seg.nrrd"))
    storage.ReadData(node)
    segmentation = node.GetSegmentation()
    segment = segmentation.GetSegment(segmentation.GetSegmentIdBySegmentName("TumorMask"))
    ijk, M = segment_labelmap(segment)
    return ijk, M, reference_geometry(segmentation)


def components(ijk):
    # face-connected (6-neighbour) components, largest first
    remaining = set(map(tuple, np.asarray(ijk).tolist()))
    steps = ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))
    found = []
    while remaining:
        start = remaining.pop()
        component, stack = [start], [start]
        while stack:
            i, j, k = stack.pop()
            for di, dj, dk in steps:
                n = (i + di, j + dj, k + dk)
                if n in remaining:
                    remaining.remove(n)
                    component.append(n)
                    stack.append(n)
        found.append(component)
    return sorted(found, key=len, reverse=True)


def dilate(ijk, M, radius_mm, geometry):
    # every voxel within radius_mm of the mask, clipped to the segmentation's
    # extent (a grown segment can't leave its geometry)
    spacing = np.linalg.norm(M[:3, :3], axis=0)
    n = np.ceil(radius_mm / spacing).astype(int)
    offsets = [(a, b, c)
               for a in range(-n[0], n[0] + 1)
               for b in range(-n[1], n[1] + 1)
               for c in range(-n[2], n[2] + 1)
               if (a * spacing[0]) ** 2 + (b * spacing[1]) ** 2 + (c * spacing[2]) ** 2
               <= radius_mm ** 2 + 1e-6]
    grown = {(p[0] + a, p[1] + b, p[2] + c)
             for p in np.asarray(ijk).tolist() for a, b, c in offsets}
    grown = np.array(sorted(grown))
    if geometry is not None and np.allclose(geometry[0], M, atol=1e-3):
        e = geometry[1]
        inside = ((grown[:, 0] >= e[0]) & (grown[:, 0] <= e[1]) &
                  (grown[:, 1] >= e[2]) & (grown[:, 1] <= e[3]) &
                  (grown[:, 2] >= e[4]) & (grown[:, 2] <= e[5]))
        grown = grown[inside]
    return grown


# --- comparing ---------------------------------------------------------------

def dice(a, b):
    if not a and not b:
        return 1.0
    return 2 * len(a & b) / (len(a) + len(b))


def expect_mask(ctx, got, want, label, min_dice=1.0):
    # exact by default: a few voxels can be the whole point (e.g. 3 islands
    # in a 1566-voxel mask still give Dice 0.999)
    d = dice(got, want)
    return ctx.expect(d >= min_dice,
                      f"{label}: {len(got)} voxels, expected {len(want)} "
                      f"({len(want - got)} missing, {len(got - want)} extra, Dice {d:.3f}, "
                      f"needs {min_dice})")


def segment_id(ctx, seg, name):
    sid = seg.GetSegmentation().GetSegmentIdBySegmentName(name)
    ctx.expect(bool(sid), f"no segment named '{name}' in '{seg.GetName()}'")
    return sid or None


def check_geometry(ctx, seg, volume):
    # the segmentation's reference geometry is the volume's voxel grid
    geometry = reference_geometry(seg.GetSegmentation())
    if not ctx.expect(geometry is not None, f"'{seg.GetName()}' has no reference geometry"):
        return
    M, extent = geometry
    m = vtk.vtkMatrix4x4()
    volume.GetIJKToRASMatrix(m)
    want_extent = list(volume.GetImageData().GetExtent())
    ctx.expect(np.allclose(M, matrix_array(m), atol=1e-3),
               f"'{seg.GetName()}' geometry has a different spacing, origin or "
               f"directions than '{volume.GetName()}'")
    ctx.expect(extent == want_extent,
               f"'{seg.GetName()}' geometry extent {extent}, expected {want_extent}")


def benchmark_ct(ctx):
    return ctx.node_from_file("vtkMRMLScalarVolumeNode", "benchmark_ct.nrrd")


def island_segmentation(ctx):
    return ctx.node_from_file("vtkMRMLSegmentationNode", "islands.seg.nrrd")


def tumor_unchanged(ctx, seg, fixture):
    sid = segment_id(ctx, seg, "TumorMask")
    if sid:
        expect_mask(ctx, segment_set(seg, sid), to_set(fixture[0], fixture[1]),
                    "TumorMask (should be unchanged)")


# --- 09-12: new segmentations on the CT --------------------------------------

# 09 — Create a segmentation for a volume
def check_09(ctx):
    ct = benchmark_ct(ctx)
    seg = ctx.one_node("vtkMRMLSegmentationNode", "Organ Segmentation")
    if ct is not None and seg is not None:
        check_geometry(ctx, seg, ct)


# 10 — Add a named segment
def check_10(ctx):
    ct = benchmark_ct(ctx)
    seg = ctx.one_node("vtkMRMLSegmentationNode", "Named Segment Test")
    if ct is None or seg is None:
        return
    check_geometry(ctx, seg, ct)
    sid = segment_id(ctx, seg, "Target Region")
    if not sid:
        return
    color = seg.GetSegmentation().GetSegment(sid).GetColor()
    ctx.expect(all(abs(c - e) <= 0.01 for c, e in zip(color, (0.2, 0.7, 0.3))),
               f"segment color {tuple(round(c, 3) for c in color)}, expected (0.2, 0.7, 0.3)")
    voxels = len(segment_set(seg, sid))
    ctx.expect(voxels == 0, f"'Target Region' should be empty, has {voxels} voxels")


# 11 — Threshold a CT volume
def check_11(ctx):
    ct = benchmark_ct(ctx)
    seg = ctx.one_node("vtkMRMLSegmentationNode", "Bone Threshold Segmentation")
    if ct is None or seg is None:
        return
    sid = segment_id(ctx, seg, "Bone")
    if sid:
        volume = read_volume(ctx.path("benchmark_ct.nrrd"))
        expect_mask(ctx, segment_set(seg, sid), range_set(volume, 300, 800),
                    "Bone (300 to 800)", min_dice=0.99)


# 12 — Threshold a volume into two segments
def check_12(ctx):
    ct = benchmark_ct(ctx)
    seg = ctx.one_node("vtkMRMLSegmentationNode", "Two Range Segmentation")
    if ct is None or seg is None:
        return
    volume = read_volume(ctx.path("benchmark_ct.nrrd"))
    for name, lo, hi in (("Air", -1000, -201), ("Dense Tissue", 400, 800)):
        sid = segment_id(ctx, seg, name)
        if sid:
            expect_mask(ctx, segment_set(seg, sid), range_set(volume, lo, hi),
                        f"{name} ({lo} to {hi})", min_dice=0.99)


# --- 13-16: editing TumorMask ------------------------------------------------

# 13 — Keep the largest island
def check_13(ctx):
    seg = island_segmentation(ctx)
    if seg is None:
        return
    ijk, M, _ = fixture_tumor(ctx)
    sid = segment_id(ctx, seg, "TumorMask")
    if sid:
        expect_mask(ctx, segment_set(seg, sid), to_set(components(ijk)[0], M),
                    "TumorMask (largest island only)")


# 14 — Remove small islands
def check_14(ctx):
    seg = island_segmentation(ctx)
    if seg is None:
        return
    ijk, M, _ = fixture_tumor(ctx)
    kept = [v for c in components(ijk) if len(c) >= 4 for v in c]
    sid = segment_id(ctx, seg, "TumorMask")
    if sid:
        expect_mask(ctx, segment_set(seg, sid), to_set(kept, M),
                    "TumorMask (islands of 4+ voxels)")


# 15 — Smooth a segment
def check_15(ctx):
    # Slicer's exact Gaussian result isn't recomputed here, so this checks
    # what any 2 mm smoothing does: a new, similar but changed mask without
    # the single-voxel islands, and an untouched original
    seg = island_segmentation(ctx)
    if seg is None:
        return
    fixture = fixture_tumor(ctx)
    ijk, M, _ = fixture
    tumor_unchanged(ctx, seg, fixture)
    sid = segment_id(ctx, seg, "TumorMask Smoothed")
    if not sid:
        return
    smoothed, original = segment_set(seg, sid), to_set(ijk, M)
    if not ctx.expect(smoothed, "'TumorMask Smoothed' is empty"):
        return
    ctx.expect(smoothed != original, "'TumorMask Smoothed' is identical to TumorMask")
    d = dice(smoothed, original)
    ctx.expect(d >= 0.7, f"'TumorMask Smoothed' has Dice {d:.3f} with TumorMask, expected 0.7 or more")
    small = to_set([v for c in components(ijk)[1:] for v in c], M)
    left = len(small & smoothed)
    ctx.expect(left == 0, f"'TumorMask Smoothed' still has {left} of the {len(small)} isolated voxels")


# 16 — Grow or shrink a segment
def check_16(ctx):
    # growing by 2 mm can be done with slightly different kernels, so the
    # result has to contain everything within 1.5 mm and nothing beyond 2.5 mm
    # (1% of voxels may differ)
    seg = island_segmentation(ctx)
    if seg is None:
        return
    fixture = fixture_tumor(ctx)
    ijk, M, geometry = fixture
    tumor_unchanged(ctx, seg, fixture)
    sid = segment_id(ctx, seg, "TumorMask Grown")
    if not sid:
        return
    grown = segment_set(seg, sid)
    inner = to_set(dilate(ijk, M, 1.5, geometry), M)
    outer = to_set(dilate(ijk, M, 2.5, geometry), M)
    slack = 0.01 * len(inner)
    missing, extra = len(inner - grown), len(grown - outer)
    ctx.expect(missing <= slack,
               f"'TumorMask Grown' misses {missing} voxels within 1.5 mm of TumorMask "
               f"({len(grown)} voxels, grown too little or not on the same grid)")
    ctx.expect(extra <= slack,
               f"'TumorMask Grown' has {extra} voxels more than 2.5 mm from TumorMask "
               f"({len(grown)} voxels, grown too much)")


# --- 17-18 -------------------------------------------------------------------

# 17 — Create a segment from a labelmap
def check_17(ctx):
    labelmap = ctx.node_from_file("vtkMRMLLabelMapVolumeNode", "labelmap.nrrd")
    seg = ctx.one_node("vtkMRMLSegmentationNode", "Labelmap Segmentation")
    if labelmap is None or seg is None:
        return
    sid = segment_id(ctx, seg, "Central Label")
    if sid:
        volume = read_volume(ctx.path("labelmap.nrrd"), "vtkMRMLLabelMapVolumeNode")
        # same grid as the labelmap, or the voxel centers won't match
        expect_mask(ctx, segment_set(seg, sid), range_set(volume, 1, 1), "Central Label (label 1)")


# 18 — Create a closed surface from a segment
def check_18(ctx):
    seg = island_segmentation(ctx)
    if seg is None:
        return
    sid = segment_id(ctx, seg, "TumorMask")
    if not sid:
        return
    if not ctx.expect(seg.GetSegmentation().ContainsRepresentation("Closed surface"),
                      "segmentation has no closed-surface representation"):
        return
    surface = seg.GetClosedSurfaceInternalRepresentation(sid)
    ctx.expect(surface is not None and surface.GetNumberOfCells() > 0,
               "TumorMask's closed surface is empty")


CHECKS = {
    "09": check_09,
    "10": check_10,
    "11": check_11,
    "12": check_12,
    "13": check_13,
    "14": check_14,
    "15": check_15,
    "16": check_16,
    "17": check_17,
    "18": check_18,
}
