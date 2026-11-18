import glob
import json
import os
import tempfile
import zipfile
import xml.etree.ElementTree as ET
from urllib.parse import unquote

import numpy as np
import slicer
import vtk
from vtk.util import numpy_support

# Export and save checks (tasks 34-40).
# The result of these tasks is a file, so the checks read the exported file
# back and compare it with the fixture it came from. Files are read into a
# temporary scene (or without MRML at all), never into slicer.mrmlScene:
# the worker saves the scene as .mrb after the check, and loading files here
# would change what gets saved. The scene's own nodes are not used for the
# content either, because saving a node points its storage node at the new
# file (tasks 36, 37 and 39 only check that the node exists).


# --- helpers -----------------------------------------------------------------

def close(a, b, tol):
    return all(abs(x - y) <= tol for x, y in zip(a, b))


def fmt(p):
    return tuple(round(x, 2) for x in p)


def output_file(ctx, name):
    # the worker empties outputs/ before every task, so an existing file
    # was written during this task
    path = ctx.path(f"outputs/{name}")
    if not ctx.expect(os.path.isfile(path), f"no file at outputs/{name}"):
        return None
    return path


def loaded_and_saved(ctx, cls, fixture, export):
    # the node must be loaded into Slicer and saved from there, not made by
    # copying or writing the file by hand. Saving repoints the node's storage
    # at the new file, so accept a node whose file is the fixture or the export
    sources = {os.path.realpath(ctx.path(f)) for f in (fixture, f"outputs/{export}")}
    nodes = []
    for n in slicer.util.getNodesByClass(cls):
        storage = n.GetStorageNode()
        name = storage.GetFileName() if storage else None
        if name and os.path.realpath(name) in sources:
            nodes.append(n)
    ctx.expect(len(nodes) == 1, f"expected 1 {cls} loaded from {fixture}, found {len(nodes)}")


def volume_info(path):
    # voxels and geometry of a volume file, read into a throwaway scene
    scene = slicer.vtkMRMLScene()
    node = scene.AddNewNodeByClass("vtkMRMLScalarVolumeNode")
    storage = scene.AddNewNodeByClass("vtkMRMLVolumeArchetypeStorageNode")
    storage.SetFileName(path)
    if not storage.ReadData(node) or node.GetImageData() is None:
        return None
    m = vtk.vtkMatrix4x4()
    node.GetIJKToRASMatrix(m)
    return {"array": slicer.util.arrayFromVolume(node).copy(),
            "ijk_to_ras": [m.GetElement(i, j) for i in range(4) for j in range(4)]}


def check_volume(ctx, path, reference, label):
    # same dims, voxel values and geometry as the reference file
    got, want = volume_info(path), volume_info(ctx.path(reference))
    if not ctx.expect(got is not None, f"{label}: can't be read as a volume"):
        return False
    shape, expected = got["array"].shape[::-1], want["array"].shape[::-1]  # IJK order
    ok = ctx.expect(shape == expected, f"{label}: dims {shape}, expected {expected}")
    if ok:
        ok &= ctx.expect(np.array_equal(got["array"], want["array"]),
                         f"{label}: voxel values differ from {reference}")
    ok &= ctx.expect(close(got["ijk_to_ras"], want["ijk_to_ras"], 1e-3),
                     f"{label}: spacing, origin or directions differ from {reference}")
    return ok


def segmentation_node(scene, path):
    node = scene.AddNewNodeByClass("vtkMRMLSegmentationNode")
    storage = scene.AddNewNodeByClass("vtkMRMLSegmentationStorageNode")
    storage.SetFileName(path)
    if not storage.ReadData(node):
        return None
    return node


def segment_voxels(path):
    # {segment name: number of voxels} of a .seg.nrrd file
    scene = slicer.vtkMRMLScene()
    node = segmentation_node(scene, path)
    if node is None:
        return None
    segmentation = node.GetSegmentation()
    counts = {}
    for i in range(segmentation.GetNumberOfSegments()):
        segment_id = segmentation.GetNthSegmentID(i)
        segment = segmentation.GetSegment(segment_id)
        labelmap = slicer.util.arrayFromSegmentInternalBinaryLabelmap(node, segment_id)
        counts[segment.GetName()] = 0 if labelmap is None else int((labelmap == segment.GetLabelValue()).sum())
    return counts


def check_segmentation(ctx, path, reference, label):
    # same segments, each with the same number of voxels
    got, want = segment_voxels(path), segment_voxels(ctx.path(reference))
    if not ctx.expect(got is not None, f"{label}: can't be read as a segmentation"):
        return False
    return ctx.expect(got == want, f"{label}: segments {got}, expected {want}")


def surface_summary(polydata):
    # bounding-box center and enclosed volume of a surface
    b = polydata.GetBounds()
    center = ((b[0] + b[1]) / 2, (b[2] + b[3]) / 2, (b[4] + b[5]) / 2)
    mass = vtk.vtkMassProperties()
    mass.SetInputData(polydata)
    mass.Update()
    return center, mass.GetVolume()


def tumor_mask_surface(reference):
    # TumorMask's closed surface, made with Slicer's default conversion
    scene = slicer.vtkMRMLScene()
    node = segmentation_node(scene, reference)
    segment_id = node.GetSegmentation().GetSegmentIdBySegmentName("TumorMask")
    node.CreateClosedSurfaceRepresentation()
    polydata = vtk.vtkPolyData()
    node.GetClosedSurfaceRepresentation(segment_id, polydata)
    return polydata


def fiducials_in(path):
    # [(markup type, [(label, RAS position), ...]), ...] from a .mrk.json file
    with open(path) as f:
        data = json.load(f)
    markups = []
    for m in data.get("markups", []):
        lps = m.get("coordinateSystem", "LPS") == "LPS"  # LPS is the schema default
        points = []
        for p in m.get("controlPoints", []):
            x, y, z = p["position"]
            points.append((p.get("label"), (-x, -y, z) if lps else (x, y, z)))
        markups.append((m.get("type"), points))
    return markups


def by_layout_name(cls, name):
    for n in slicer.util.getNodesByClass(cls):
        if n.GetLayoutName() == name:
            return n
    return None


# --- 34-35: whole scenes -----------------------------------------------------

def mrml_storage_file(nodes, element, mrml_dir):
    # file of a data node's storage node; MRML paths are relative to the .mrml
    ids = []
    for part in element.get("references", "").split(";"):
        role, _, value = part.partition(":")
        if role.strip() == "storage":
            ids += value.split()
    ids += element.get("storageNodeRef", "").split()  # older MRML files
    for storage_id in ids:
        storage = nodes.get(storage_id)
        if storage is not None and storage.get("fileName"):
            return os.path.normpath(os.path.join(mrml_dir, unquote(storage.get("fileName"))))
    return None


def check_scene_data(ctx, nodes, mrml_dir, root, tag, name, check, reference):
    # one data node with this name, whose file is inside the saved scene's
    # folder and has the same content as the reference
    elements = [e for e in nodes.values() if e.tag == tag and e.get("name") == name]
    if not ctx.expect(len(elements) == 1,
                      f"scene file has {len(elements)} {tag} nodes named '{name}', expected 1"):
        return
    path = mrml_storage_file(nodes, elements[0], mrml_dir)
    if not ctx.expect(path is not None, f"'{name}' has no data file in the scene"):
        return
    if not ctx.expect(os.path.isfile(path), f"'{name}' data file missing: {path}"):
        return
    root = os.path.realpath(root)
    if not ctx.expect(os.path.realpath(path).startswith(root + os.sep),
                      f"'{name}' data file is outside the saved scene: {path}"):
        return
    check(ctx, path, reference, f"'{name}' data file")


def check_scene(ctx, mrml_path, root):
    try:
        nodes = {e.get("id"): e for e in ET.parse(mrml_path).getroot() if e.get("id")}
    except ET.ParseError as e:
        ctx.expect(False, f"scene file can't be parsed: {e}")
        return
    mrml_dir = os.path.dirname(mrml_path)
    check_scene_data(ctx, nodes, mrml_dir, root, "Volume", "Benchmark CT",
                     check_volume, "benchmark_ct.nrrd")
    check_scene_data(ctx, nodes, mrml_dir, root, "Segmentation", "Island Segmentation",
                     check_segmentation, "islands.seg.nrrd")


# 34 — Save the full scene as MRB
def check_34(ctx):
    path = output_file(ctx, "benchmark_scene.mrb")
    if path is None:
        return
    if not ctx.expect(zipfile.is_zipfile(path), "benchmark_scene.mrb is not a zip archive"):
        return
    with tempfile.TemporaryDirectory() as tmp:
        with zipfile.ZipFile(path) as bundle:
            bundle.extractall(tmp)
        scenes = glob.glob(os.path.join(tmp, "**", "*.mrml"), recursive=True)
        if not ctx.expect(len(scenes) == 1, f"bundle has {len(scenes)} .mrml files, expected 1"):
            return
        check_scene(ctx, scenes[0], tmp)


# 35 — Save the scene as MRML
def check_35(ctx):
    path = output_file(ctx, "benchmark_scene/Scene.mrml")
    if path is None:
        return
    # data files have to be saved next to the scene, not left in test_files
    check_scene(ctx, path, os.path.dirname(path))


# --- 36-39: single nodes -----------------------------------------------------

# 36 — Export a volume to NRRD
def check_36(ctx):
    loaded_and_saved(ctx, "vtkMRMLScalarVolumeNode", "benchmark_ct.nrrd", "benchmark_ct_export.nrrd")
    path = output_file(ctx, "benchmark_ct_export.nrrd")
    if path is not None:
        check_volume(ctx, path, "benchmark_ct.nrrd", "benchmark_ct_export.nrrd")


# 37 — Export a segmentation to SEG.NRRD
def check_37(ctx):
    loaded_and_saved(ctx, "vtkMRMLSegmentationNode", "islands.seg.nrrd",
                     "island_segmentation_export.seg.nrrd")
    path = output_file(ctx, "island_segmentation_export.seg.nrrd")
    if path is not None:
        check_segmentation(ctx, path, "islands.seg.nrrd", "island_segmentation_export.seg.nrrd")


# 38 — Export a segment as STL
def check_38(ctx):
    path = output_file(ctx, "tumor_mask.stl")
    if path is None:
        return
    reader = vtk.vtkSTLReader()
    reader.SetFileName(path)
    reader.Update()
    surface = reader.GetOutput()
    if not ctx.expect(surface.GetNumberOfCells() > 0, "tumor_mask.stl has no triangles"):
        return
    center, volume = surface_summary(surface)
    want_center, want_volume = surface_summary(tumor_mask_surface(ctx.path("islands.seg.nrrd")))
    # Slicer writes STL in LPS by default, so accept the surface in either system
    lps_center = (-want_center[0], -want_center[1], want_center[2])
    ctx.expect(close(center, want_center, 2) or close(center, lps_center, 2),
               f"surface centered at {fmt(center)}, expected {fmt(want_center)} (RAS) "
               f"or {fmt(lps_center)} (LPS)")
    # loose, so other smoothing settings still count
    ctx.expect(abs(volume - want_volume) <= 0.15 * want_volume,
               f"surface encloses {volume:.0f} mm3, expected about {want_volume:.0f}")


# 39 — Export markups to JSON
def check_39(ctx):
    loaded_and_saved(ctx, "vtkMRMLMarkupsFiducialNode", "fiducials.mrk.json",
                     "fiducials_export.mrk.json")
    path = output_file(ctx, "fiducials_export.mrk.json")
    if path is None:
        return
    try:
        got = fiducials_in(path)
    except (ValueError, KeyError, TypeError) as e:
        ctx.expect(False, f"fiducials_export.mrk.json can't be read: {e!r}")
        return
    want = fiducials_in(ctx.path("fiducials.mrk.json"))
    if not ctx.expect(len(got) == 1, f"file has {len(got)} markups, expected 1"):
        return
    (kind, points), (_, want_points) = got[0], want[0]
    ctx.expect(kind == "Fiducial", f"markup type {kind}, expected Fiducial")
    if not ctx.expect(len(points) == len(want_points),
                      f"{len(points)} points, expected {len(want_points)}"):
        return
    for (label, p), (want_label, q) in zip(points, want_points):
        ctx.expect(label == want_label and close(p, q, 0.01),
                   f"point '{label}' at {fmt(p)}, expected '{want_label}' at {fmt(q)} (RAS)")


# --- 40: screenshot ----------------------------------------------------------

# 40 — Capture a view as an image
def check_40(ctx):
    ct = ctx.node_from_file("vtkMRMLScalarVolumeNode", "benchmark_ct.nrrd")
    if ct is not None:
        composite = by_layout_name("vtkMRMLSliceCompositeNode", "Red")
        ctx.expect(composite is not None and composite.GetBackgroundVolumeID() == ct.GetID(),
                   "Red view isn't showing the CT")

    path = output_file(ctx, "red_slice.png")
    if path is None:
        return
    reader = vtk.vtkPNGReader()
    if not ctx.expect(reader.CanReadFile(path), "red_slice.png is not a PNG"):
        return
    reader.SetFileName(path)
    reader.Update()
    image = reader.GetOutput()
    width, height, _ = image.GetDimensions()
    pixels = numpy_support.vtk_to_numpy(image.GetPointData().GetScalars())
    ctx.expect(pixels.max() > pixels.min(), "red_slice.png is a blank image")

    # a capture of the Red view has its shape (with or without the bar on
    # top); a capture of the whole window usually doesn't. Pixel sizes can
    # differ on high-DPI screens, so compare aspect ratios
    widget = slicer.app.layoutManager().sliceWidget("Red")
    ratios = [w.width / w.height for w in (widget.sliceView(), widget) if w.height]
    ratio = width / height if height else 0
    ctx.expect(any(abs(ratio - r) <= 0.02 * r for r in ratios),
               f"image is {width}x{height}, which isn't the shape of the Red view "
               f"(aspect {ratio:.2f}, expected {' or '.join(f'{r:.2f}' for r in ratios)})")


CHECKS = {
    "34": check_34,
    "35": check_35,
    "36": check_36,
    "37": check_37,
    "38": check_38,
    "39": check_39,
    "40": check_40,
}
