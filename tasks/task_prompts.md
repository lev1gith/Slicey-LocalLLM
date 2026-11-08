## Load and organize data

### 01 — Load a NRRD volume
Load the volume from `{fixture_path}` into the scene. Name the volume `{volume_name}`. Do not load any other data.

### 02 — Load a NIfTI volume
Load the volume from `{fixture_path}` into the scene. Name the volume `{volume_name}`. Do not load any other data.

### 03 — Import a DICOM series
Import the DICOM series in `{dicom_directory}` and load the series identified as `{series_description}` (series UID: `{series_uid}`) as a volume named `{volume_name}`.

### 04 — Load a saved segmentation
Load the segmentation from `{fixture_path}` into the scene and name it `{segmentation_name}`.

### 05 — Load a surface model
Load the surface model from `{fixture_path}` into the scene and name it `{model_name}`.

### 06 — Load markups from JSON
Load the markup file `{fixture_path}` into the scene. Name the markup node `{markup_name}`.

### 07 — Summarize the scene
Create a concise scene summary at `{output_path}`. For every node in the scene, include its name and node type. Include these expected nodes: `{expected_nodes}`.

### 08 — Load MRHead sample data
Use Slicer's Sample Data module to download and load the sample data named `MRHead`. Name the resulting volume `MRHead`.

## Create and edit segmentations

### 09 — Create a segmentation for a volume
Create a segmentation node named `{segmentation_name}` using `{volume_name}` as its source volume. Ensure the segmentation uses the source volume's geometry.

### 10 — Add a named segment
In segmentation `{segmentation_name}`, add an empty segment named `{segment_name}` with color `{color_rgb}` (RGB values from 0 to 1).

### 11 — Threshold a CT volume
In volume `{volume_name}`, create a segment named `{segment_name}` containing voxels with intensity from `{lower_threshold}` through `{upper_threshold}`. Store it in segmentation `{segmentation_name}`.

### 12 — Threshold a volume into two segments
In volume `{volume_name}`, create two segments in `{segmentation_name}`: `{segment_a_name}` for intensities `{a_lower}` through `{a_upper}`, and `{segment_b_name}` for intensities `{b_lower}` through `{b_upper}`. Keep the segments separate.

### 13 — Keep the largest island
In segmentation `{segmentation_name}`, keep only the largest connected component of segment `{segment_name}`. Remove the other components.

### 14 — Remove small islands
In segmentation `{segmentation_name}`, remove connected components smaller than `{minimum_voxels}` voxels from segment `{segment_name}`. Keep components at or above that size.

### 15 — Smooth a segment
Smooth segment `{segment_name}` in segmentation `{segmentation_name}` using the `{smoothing_method}` method with a kernel size of `{kernel_size_mm}` mm. Save the result as `{output_segment_name}`.

### 16 — Grow or shrink a segment
In segmentation `{segmentation_name}`, `{operation}` segment `{segment_name}` by `{margin_mm}` mm. Save the result as `{output_segment_name}` and preserve the segmentation's source geometry. Use `grow` or `shrink` for `{operation}`.

### 17 — Create a segment from a labelmap
Load labelmap `{fixture_path}` and create a segmentation named `{segmentation_name}` from label value `{label_value}`. Name the resulting segment `{segment_name}` and preserve the labelmap geometry.

### 18 — Create a closed surface from a segment
Create a closed-surface representation for segment `{segment_name}` in segmentation `{segmentation_name}`.

## Measure and annotate

### 19 — Place a markup point
Create a markups point list named `{markup_name}` with one point at RAS coordinate ({ras_x}, {ras_y}, {ras_z}) mm.

### 20 — Measure a line between two points
Create a line markup named `{markup_name}` with endpoints at RAS coordinates ({start_x}, {start_y}, {start_z}) mm and ({end_x}, {end_y}, {end_z}) mm.

### 21 — Measure an angle
Create an angle markup named `{markup_name}` with points at RAS coordinates ({point_a_x}, {point_a_y}, {point_a_z}), ({vertex_x}, {vertex_y}, {vertex_z}), and ({point_c_x}, {point_c_y}, {point_c_z}) mm, in that order.

### 22 — Create a curve markup
Create a curve markup named `{markup_name}` passing through these RAS control points in order: `{ras_control_points}` (coordinates in mm).

### 23 — Create a region of interest
Create an ROI markup named `{roi_name}` centered at RAS coordinate ({center_x}, {center_y}, {center_z}) mm, with size ({size_x}, {size_y}, {size_z}) mm.

### 24 — Compute segment statistics
For segment `{segment_name}` in segmentation `{segmentation_name}`, compute its volume and the mean intensity of volume `{volume_name}` inside the segment. Save the results in a table named `{table_name}`.

### 25 — Measure a segment's volume
Measure the volume of segment `{segment_name}` in segmentation `{segmentation_name}` and save the result in a table named `{table_name}`.

## Configure views and display

### 26 — Set the four-up layout
Set the Slicer layout to `{layout_name}`, the four-view arrangement containing the Red, Yellow, Green, and 3D views.

### 27 — Show a volume in slice views
Set `{volume_name}` as the background volume in the Red, Yellow, and Green slice views.

### 28 — Set slice orientation
Set slice view `{slice_view}` to `{orientation}` orientation. Use `Axial`, `Coronal`, or `Sagittal` for `{orientation}`.

### 29 — Set slice position
Set slice view `{slice_view}` to physical offset `{offset_mm}` mm.

### 30 — Set window and level
For volume `{volume_name}`, set the display window to `{window}` and level to `{level}`.

### 31 — Show a segmentation in 3D
Display segmentation `{segmentation_name}` in the 3D view. Make sure its closed-surface representation is visible.

### 32 — Set model display properties
For model `{model_name}`, set its display color to `{color_rgb}` (RGB values from 0 to 1) and opacity to `{opacity}` (from 0 to 1).

### 33 — Enable volume rendering
Enable volume rendering for volume `{volume_name}` and make the rendered volume visible in the 3D view.

## Save and export results

### 34 — Save the full scene as MRB
Save the complete scene as a Slicer bundle at `{output_path}`.

### 35 — Save the scene as MRML
Save the scene as an MRML scene at `{output_path}`, including its referenced data files in the requested output directory.

### 36 — Export a volume to NRRD
Save volume `{volume_name}` as a NRRD file at `{output_path}`.

### 37 — Export a segmentation to SEG.NRRD
Save segmentation `{segmentation_name}` as a `.seg.nrrd` file at `{output_path}`.

### 38 — Export a segment as STL
Export segment `{segment_name}` from segmentation `{segmentation_name}` as an STL surface file at `{output_path}`.

### 39 — Export markups to JSON
Save markup node `{markup_name}` as a JSON file at `{output_path}`.

### 40 — Capture a view as an image
Capture the `{view_name}` view and save it as an image at `{output_path}`.
