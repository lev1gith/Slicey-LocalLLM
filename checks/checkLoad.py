import os

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


CHECKS = {
    "01": check_01,
}
