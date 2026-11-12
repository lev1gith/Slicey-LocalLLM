### 01 — Load a NRRD volume
Load `{TEST_FILES}/MRHead.nrrd` into the scene as a volume named `MRHead NRRD`. Do not load any other data.

### 02 — Load a NIfTI volume
Load `{TEST_FILES}/brain.nii.gz` into the scene as a volume named `Brain NIfTI`. Do not load any other data.

### 03 — Import a DICOM series
Import the DICOM series from `{TEST_FILES}/dicom_series` and load the series whose description is `Synthetic Test CT` as a volume named `Synthetic DICOM CT`. Do not load any other data.

### 04 — Load a saved segmentation
Load `{TEST_FILES}/islands.seg.nrrd` into the scene as a segmentation named `Island Segmentation`. Do not load any other data.

### 05 — Load a surface model
Load `{TEST_FILES}/sphere_model.stl` into the scene as a model named `Benchmark Sphere`. Do not load any other data.

### 06 — Load markups from JSON
Load `{TEST_FILES}/fiducials.mrk.json` into the scene as a markup node named `Benchmark Fiducials`. Do not load any other data.

### 07 — Summarize the scene
Load `{TEST_FILES}/benchmark_ct.nrrd` as `Benchmark CT`, `{TEST_FILES}/islands.seg.nrrd` as `Island Segmentation`, `{TEST_FILES}/sphere_model.stl` as `Benchmark Sphere`, and `{TEST_FILES}/fiducials.mrk.json` as `Benchmark Fiducials`. Write a concise scene summary to `{TEST_FILES}/outputs/scene_summary.txt`, listing every node's name and node type. Include the four named nodes above.

### 08 — Load MRHead sample data
Use Slicer's Sample Data module to download and load the sample data named `MRHead`. Name the resulting volume `MRHead`.

### 09 — Create a segmentation for a volume
Load `{TEST_FILES}/benchmark_ct.nrrd` as `Benchmark CT`. Create a segmentation named `Organ Segmentation` using `Benchmark CT` as its source volume, with the same geometry.

### 10 — Add a named segment
Load `{TEST_FILES}/benchmark_ct.nrrd` as `Benchmark CT`. Create a segmentation named `Named Segment Test` using that volume's geometry, then add an empty segment named `Target Region` with RGB color (0.2, 0.7, 0.3).

### 11 — Threshold a CT volume
Load `{TEST_FILES}/benchmark_ct.nrrd` as `Benchmark CT`. Create a segmentation named `Bone Threshold Segmentation` and add a segment named `Bone` containing voxels in `Benchmark CT` with intensities from 300 through 800.

### 12 — Threshold a volume into two segments
Load `{TEST_FILES}/benchmark_ct.nrrd` as `Benchmark CT`. Create a segmentation named `Two Range Segmentation` with separate segments: `Air` for intensities -1000 through -201 and `Dense Tissue` for intensities 400 through 800.

### 13 — Keep the largest island
Load `{TEST_FILES}/islands.seg.nrrd` as `Island Segmentation`. In its `TumorMask` segment, keep only the largest connected component and remove the smaller components.

### 14 — Remove small islands
Load `{TEST_FILES}/islands.seg.nrrd` as `Island Segmentation`. In its `TumorMask` segment, remove connected components smaller than 4 voxels and keep components of 4 voxels or larger.

### 15 — Smooth a segment
Load `{TEST_FILES}/islands.seg.nrrd` as `Island Segmentation`. Smooth its `TumorMask` segment using the Gaussian method with a 2 mm kernel, saving the result as a separate segment named `TumorMask Smoothed`.

### 16 — Grow or shrink a segment
Load `{TEST_FILES}/islands.seg.nrrd` as `Island Segmentation`. Grow its `TumorMask` segment by 2 mm and save the result as a separate segment named `TumorMask Grown`, preserving the segmentation geometry.

### 17 — Create a segment from a labelmap
Load `{TEST_FILES}/labelmap.nrrd` as a labelmap. Create a segmentation named `Labelmap Segmentation` from label value 1, name the resulting segment `Central Label`, and preserve the labelmap geometry.

### 18 — Create a closed surface from a segment
Load `{TEST_FILES}/islands.seg.nrrd` as `Island Segmentation` and create a closed-surface representation for its `TumorMask` segment.

### 19 — Place a markup point
Create a Markups point list named `Target Point` with one point at RAS coordinate (5, 10, 15) mm.

### 20 — Measure a line between two points
Create a line markup named `50 mm Test Line` with endpoints at RAS coordinates (0, 0, 0) mm and (30, 40, 0) mm.

### 21 — Measure an angle
Create an angle markup named `Right Angle Test` with points at RAS coordinates (1, 0, 0), (0, 0, 0), and (0, 1, 0) mm, in that order.

### 22 — Create a curve markup
Create a curve markup named `Benchmark Curve` passing through these RAS control points in order: (0, 0, 0), (10, 5, 0), (20, 0, 5), and (30, 5, 10) mm.

### 23 — Create a region of interest
Create an ROI markup named `Benchmark ROI` centered at RAS coordinate (0, 0, 0) mm, with size (20, 30, 40) mm.

### 24 — Compute segment statistics
Load `{TEST_FILES}/benchmark_ct.nrrd` as `Benchmark CT` and `{TEST_FILES}/islands.seg.nrrd` as `Island Segmentation`. For segment `TumorMask`, compute its volume and the mean intensity of `Benchmark CT` inside the segment. Save the results in a table named `Tumor Statistics`.

### 25 — Measure a segment's volume
Load `{TEST_FILES}/islands.seg.nrrd` as `Island Segmentation`. Measure the volume of its `TumorMask` segment and save the result in a table named `Tumor Volume`.

### 26 — Set the four-up layout
Set the Slicer layout to `SlicerLayoutFourUpView`, the four-view arrangement containing the Red, Yellow, Green, and 3D views.

### 27 — Show a volume in slice views
Load `{TEST_FILES}/benchmark_ct.nrrd` as `Benchmark CT` and set it as the background volume in the Red, Yellow, and Green slice views.

### 28 — Set slice orientation
Load `{TEST_FILES}/benchmark_ct.nrrd` as `Benchmark CT`, show it in the Red slice view, and set that view to `Sagittal` orientation.

### 29 — Set slice position
Load `{TEST_FILES}/benchmark_ct.nrrd` as `Benchmark CT`, show it in the Red slice view, and set that view to physical offset 5 mm.

### 30 — Set window and level
Load `{TEST_FILES}/benchmark_ct.nrrd` as `Benchmark CT` and set its display window to 1600 and level to 300.

### 31 — Show a segmentation in 3D
Load `{TEST_FILES}/islands.seg.nrrd` as `Island Segmentation`, create its closed-surface representation, and display the `TumorMask` segment in the 3D view.

### 32 — Set model display properties
Load `{TEST_FILES}/sphere_model.stl` as `Benchmark Sphere`. Set its display color to RGB (0.1, 0.4, 0.9) and opacity to 0.65.

### 33 — Enable volume rendering
Load `{TEST_FILES}/benchmark_ct.nrrd` as `Benchmark CT`, enable volume rendering for it, and make the rendered volume visible in the 3D view.

### 34 — Save the full scene as MRB
Load `{TEST_FILES}/benchmark_ct.nrrd` as `Benchmark CT` and `{TEST_FILES}/islands.seg.nrrd` as `Island Segmentation`. Save the complete scene as a Slicer bundle at `{TEST_FILES}/outputs/benchmark_scene.mrb`.

### 35 — Save the scene as MRML
Load `{TEST_FILES}/benchmark_ct.nrrd` as `Benchmark CT` and `{TEST_FILES}/islands.seg.nrrd` as `Island Segmentation`. Save the scene as `{TEST_FILES}/outputs/benchmark_scene/Scene.mrml`, including its referenced data files in that output directory.

### 36 — Export a volume to NRRD
Load `{TEST_FILES}/benchmark_ct.nrrd` as `Benchmark CT` and save it as a NRRD file at `{TEST_FILES}/outputs/benchmark_ct_export.nrrd`.

### 37 — Export a segmentation to SEG.NRRD
Load `{TEST_FILES}/islands.seg.nrrd` as `Island Segmentation` and save it as a `.seg.nrrd` file at `{TEST_FILES}/outputs/island_segmentation_export.seg.nrrd`.

### 38 — Export a segment as STL
Load `{TEST_FILES}/islands.seg.nrrd` as `Island Segmentation`, create its closed-surface representation, and export the `TumorMask` segment as an STL surface file at `{TEST_FILES}/outputs/tumor_mask.stl`.

### 39 — Export markups to JSON
Load `{TEST_FILES}/fiducials.mrk.json` as `Benchmark Fiducials` and save that markup node as a JSON file at `{TEST_FILES}/outputs/fiducials_export.mrk.json`.

### 40 — Capture a view as an image
Load `{TEST_FILES}/benchmark_ct.nrrd` as `Benchmark CT`, show it in the Red slice view, and save a screenshot of the Red slice view to `{TEST_FILES}/outputs/red_slice.png`.
