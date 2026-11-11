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



CHECKS = {
    "01": check_01,
    "02": check_02,
    "03": check_03,
}
