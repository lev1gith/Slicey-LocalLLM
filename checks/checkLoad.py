import os
import slicer

TEST_FILES = "/Users/leventel/Desktop/personalCode/slicey_proj/test_files"


# 01 — Load a NRRD volume
def check_01(ctx):
    vol = ctx.one_node("vtkMRMLScalarVolumeNode", "MRHead NRRD")
    if vol is None:
        return  # one_node already recorded the failure

    image = vol.GetImageData()
    if ctx.expect(image is not None, "volume has no image data"):
        # sizes from the NRRD header of MRHead.nrrd
        ctx.expect(image.GetDimensions() == (256, 256, 130),
                   f"wrong dimensions {image.GetDimensions()}")

    # loaded from the given file, not e.g. the MRHead sample data download
    # (same dimensions, and its cache file is also named MRHead.nrrd)
    storage = vol.GetStorageNode()
    path = storage.GetFileName() if storage else None
    ctx.expect(path is not None and os.path.realpath(path)
               == os.path.realpath(f"{TEST_FILES}/MRHead.nrrd"),
               f"not loaded from the test file (source: {path})")

    # "Do not load any other data."
    ctx.expect(ctx.count_data_nodes() == 1,
               f"expected 1 data node, found {ctx.count_data_nodes()}")


def check_02(ctx):
    vol = ctx.one_node("vtkMRMLScalarVolumeNode", "Brain NIfTI")
    if vol is None:
        return
    image = vol.GetImageData()

    # check dimensions of loaded data
    if ctx.expect(image is not None, "volume has no image data"):
        ctx.expect(image.GetDimensions() == (286, 286, 90),
                   f"wrong dimensions {image.GetDimensions()}")

    # check load given file
    storage = vol.GetStorageNode()
    path = storage.GetFileName() if storage else None
    ctx.expect(path is not None and os.path.realpath(path)
               == os.path.realpath(f"{TEST_FILES}/brain.nii.gz"),
               f"not loaded from the test file {path}")

    # is other data besides requsted loaded?
    ctx.expect(ctx.count_data_nodes() == 1,
               f"expected 1 data node, found {ctx.count_data_nodes()}")


def check_03(ctx):
    EXPECTED_SLICES = 3
    vol = ctx.one_node("vtkMRMLScalarVolumeNode", "Synthetic DICOM CT")
    if vol is None:
        return

    attr = vol.GetAttribute("DICOM.instanceUIDs")
    if not ctx.expect(attr, "volume was not loaded from DICOM"):
        return
    uids = attr.split()

    # every slice originates from right series
    db = slicer.dicomDatabase
    descs = {db.fileValue(db.fileForInstance(u), "0008,103E").strip() for u in uids}
    ctx.expect(descs == {"Synthetic Test CT"}, f"slices from series {descs}")
    ctx.expect(len(uids) == EXPECTED_SLICES, f"{len(uids)}/{EXPECTED_SLICES} slices loaded")
    dims = vol.GetImageData().GetDimensions() if vol.GetImageData() else None
    ctx.expect(dims is not None and dims[2] == EXPECTED_SLICES, f"image has dims {dims}")

    # nothing else loaded
    ctx.expect(ctx.count_data_nodes() == 1, f"expected 1 data node, found {ctx.count_data_nodes()}")


# helpers for 04-08

def loaded_from(ctx, node, filename):
    # node's storage node points at TEST_FILES/filename
    storage = node.GetStorageNode()
    path = storage.GetFileName() if storage else None
    return ctx.expect(
        path is not None
        and os.path.realpath(path) == os.path.realpath(f"{TEST_FILES}/{filename}"),
        f"'{node.GetName()}' not loaded from {filename} (source: {path})")


# fixture facts, read from the files in test_files/
SEGMENT_NAME = "TumorMask"   # islands.seg.nrrd: the only segment
SPHERE_TRIANGLES = 224       # sphere_model.stl: number of facets
FIDUCIALS = [                # fiducials.mrk.json: label, RAS position
    ("Anterior", (0.0, 20.0, 0.0)),
    ("Center", (0.0, 0.0, 0.0)),
    ("Posterior", (0.0, -20.0, 0.0)),
]


def check_segmentation(ctx, name):
    seg = ctx.one_node("vtkMRMLSegmentationNode", name)
    if seg is None:
        return
    loaded_from(ctx, seg, "islands.seg.nrrd")
    segmentation = seg.GetSegmentation()
    ctx.expect(segmentation.GetNumberOfSegments() == 1,
               f"expected 1 segment, found {segmentation.GetNumberOfSegments()}")
    seg_id = segmentation.GetSegmentIdBySegmentName(SEGMENT_NAME)
    if ctx.expect(seg_id, f"no segment named '{SEGMENT_NAME}'"):
        # the internal labelmap needs no reference volume (task 04 has none)
        labelmap = slicer.util.arrayFromSegmentInternalBinaryLabelmap(seg, seg_id)
        ctx.expect(labelmap is not None and labelmap.any(),
                   f"segment '{SEGMENT_NAME}' is empty")


def check_model(ctx, name):
    model = ctx.one_node("vtkMRMLModelNode", name)
    if model is None:
        return
    loaded_from(ctx, model, "sphere_model.stl")
    poly = model.GetPolyData()
    cells = poly.GetNumberOfCells() if poly else 0
    ctx.expect(cells == SPHERE_TRIANGLES,
               f"expected {SPHERE_TRIANGLES} triangles, found {cells}")


def check_fiducials(ctx, name):
    markups = ctx.one_node("vtkMRMLMarkupsFiducialNode", name)
    if markups is None:
        return
    loaded_from(ctx, markups, "fiducials.mrk.json")
    n = markups.GetNumberOfControlPoints()
    if not ctx.expect(n == len(FIDUCIALS), f"expected {len(FIDUCIALS)} points, found {n}"):
        return
    for i, (label, expected) in enumerate(FIDUCIALS):
        pos = markups.GetNthControlPointPosition(i)
        ctx.expect(markups.GetNthControlPointLabel(i) == label,
                   f"point {i}: label '{markups.GetNthControlPointLabel(i)}', expected '{label}'")
        ctx.expect(all(abs(a - b) < 1e-3 for a, b in zip(pos, expected)),
                   f"point {i} ({label}) at {tuple(round(p, 3) for p in pos)}, expected {expected}")


# 04 — Load a saved segmentation
def check_04(ctx):
    check_segmentation(ctx, "Island Segmentation")
    ctx.expect(ctx.count_data_nodes() == 1, f"expected 1 data node, found {ctx.count_data_nodes()}")


# 05 — Load a surface model
def check_05(ctx):
    check_model(ctx, "Benchmark Sphere")
    ctx.expect(ctx.count_data_nodes() == 1, f"expected 1 data node, found {ctx.count_data_nodes()}")


# 06 — Load markups from JSON
def check_06(ctx):
    check_fiducials(ctx, "Benchmark Fiducials")
    ctx.expect(ctx.count_data_nodes() == 1, f"expected 1 data node, found {ctx.count_data_nodes()}")


# 07 — Summarize the scene
SUMMARY_FILE = f"{TEST_FILES}/outputs/scene_summary.txt"
# words that count as naming each node's type in the summary
SUMMARY_NODES = {
    "Benchmark CT": ("volume",),
    "Island Segmentation": ("segmentation",),
    "Benchmark Sphere": ("model",),
    "Benchmark Fiducials": ("markup", "fiducial", "point"),
}


def check_07(ctx):
    # the four loads
    ct = ctx.one_node("vtkMRMLScalarVolumeNode", "Benchmark CT")
    if ct is not None:
        loaded_from(ctx, ct, "benchmark_ct.nrrd")
        image = ct.GetImageData()
        ctx.expect(image is not None and image.GetDimensions() == (48, 48, 32),
                   f"'Benchmark CT' has dims {image.GetDimensions() if image else None}")
    check_segmentation(ctx, "Island Segmentation")
    check_model(ctx, "Benchmark Sphere")
    check_fiducials(ctx, "Benchmark Fiducials")
    ctx.expect(ctx.count_data_nodes() == 4, f"expected 4 data nodes, found {ctx.count_data_nodes()}")

    # the summary file (the worker must empty outputs/ before each task,
    # or a file from an earlier run would pass this)
    if not ctx.expect(os.path.isfile(SUMMARY_FILE), f"{SUMMARY_FILE} not written"):
        return
    with open(SUMMARY_FILE, encoding="utf-8", errors="replace") as f:
        lines = f.read().splitlines()
    for name, type_words in SUMMARY_NODES.items():
        name_lines = [line for line in lines if name in line]
        if not ctx.expect(name_lines, f"summary does not mention '{name}'"):
            continue
        # the type must be on the same line as the name, not just inside it
        # ("Island Segmentation" contains "segmentation" by itself)
        rest = " ".join(line.replace(name, "") for line in name_lines).lower()
        ctx.expect(any(w in rest for w in type_words),
                   f"summary gives no node type for '{name}'")


# 08 — Load MRHead sample data
def check_08(ctx):
    vol = ctx.one_node("vtkMRMLScalarVolumeNode", "MRHead")
    if vol is None:
        return
    image = vol.GetImageData()
    if ctx.expect(image is not None, "volume has no image data"):
        ctx.expect(image.GetDimensions() == (256, 256, 130),
                   f"wrong dimensions {image.GetDimensions()}")

    # Slicer 5.13's Sample Data leaves the volume without a storage node,
    # while loading the test file gives one that points at it.
    storage = vol.GetStorageNode()
    path = storage.GetFileName() if storage else None
    ctx.expect(path is None
               or os.path.realpath(path) != os.path.realpath(f"{TEST_FILES}/MRHead.nrrd"),
               f"loaded from test_files/MRHead.nrrd, not via Sample Data (source: {path})")

    ctx.expect(ctx.count_data_nodes() == 1, f"expected 1 data node, found {ctx.count_data_nodes()}")


CHECKS = {
    "01": check_01,
    "02": check_02,
    "03": check_03,
    "04": check_04,
    "05": check_05,
    "06": check_06,
    "07": check_07,
    "08": check_08,
}
