# Starter 3D Slicer benchmark tasks

These 40 tasks are candidates for the benchmark. Each should start from a documented, clean scene and use public sample data or a small generated fixture. The check column describes a possible automatic pass condition; refine prompts, fixtures, and tolerances before treating a task as final.

## Load and organize data

1. **Load a NRRD volume** — The expected scalar volume node exists and its dimensions match the fixture.
2. **Load a NIfTI volume** — The volume node exists and its dimensions and spacing match the fixture.
3. **Import a DICOM series** — The expected series is present in the DICOM hierarchy and loads as a volume.
4. **Load a saved segmentation** — The segmentation node contains the expected segment names and label values.
5. **Load a surface model** — The model node exists and contains non-empty polydata.
6. **Load markups from JSON** — The markup node has the expected type and control-point count.
7. **Summarize the scene** — A report lists the expected nodes, node types, and names.
8. **Load MRhead sample data** — Load the sample data MRHead.

## Create and edit segmentations

9. **Create a segmentation for a volume** — A segmentation node exists and references the requested source volume geometry.
10. **Add a named segment** — The segment exists with the requested name and color.
11. **Threshold a CT volume** — A segment is created from the requested intensity range and contains voxels.
12. **Threshold a volume into two segments** — Both requested ranges produce distinct, non-empty segments.
13. **Keep the largest island** — The output segment contains one connected component and is smaller than or equal to the input.
14. **Remove small islands** — No connected component below the requested voxel threshold remains.
15. **Smooth a segment** — The smoothed segment exists, preserves its reference geometry, and has a non-zero voxel count.
16. **Grow or shrink a segment** — The output segment changes by the requested margin direction and preserves geometry.
17. **Create a segment from a labelmap** — The segmentation contains the expected segment and matches the labelmap geometry.
18. **Create a closed surface from a segment** — The segment has a non-empty closed-surface representation.

## Measure and annotate

19. **Place a markup point** — A point list has one control point at the requested RAS coordinate within tolerance.
20. **Measure a line between two points** — A line markup has two requested endpoints and the expected length within tolerance.
21. **Measure an angle** — An angle markup has the requested three points and computed angle within tolerance.
22. **Create a curve markup** — The curve has the requested control points and a non-zero length.
23. **Create a region of interest** — The ROI has the requested center and dimensions within tolerance.
24. **Compute segment statistics** — The output table contains the requested segment's volume and mean intensity.
25. **Measure a segment's volume** — The reported volume matches the fixture's expected volume within tolerance.

## Configure views and display

26. **Set the four-up layout** — The layout node uses the requested four-view arrangement.
27. **Show a volume in slice views** — The requested background volume is assigned to the slice composites.
28. **Set slice orientation** — The requested slice view has the expected axial, coronal, or sagittal orientation.
29. **Set slice position** — The slice offset matches the requested physical position within tolerance.
30. **Set window and level** — The volume display node has the requested window and level values.
31. **Show a segmentation in 3D** — The segmentation's closed surface is visible in the 3D view.
32. **Set model display properties** — The model display node has the requested color and opacity.
33. **Enable volume rendering** — A volume-rendering display node exists for the requested volume and is enabled.

## Save and export results

34. **Save the full scene as MRB** — The bundle file exists, is non-empty, and can be reopened with the expected nodes.
35. **Save the scene as MRML** — The scene file and referenced data files exist and the scene can be reopened.
36. **Export a volume to NRRD** — The file exists and reloads with the expected dimensions and spacing.
37. **Export a segmentation to SEG.NRRD** — The file exists and reloads with the expected segment names and geometry.
38. **Export a segment as STL** — The mesh file exists, is non-empty, and reloads with non-empty polydata.
39. **Export markups to JSON** — The file exists and contains the expected markup type and control points.
40. **Capture a view as an image** — The screenshot file exists, has non-zero dimensions, and is not blank.

## Benchmark notes

- Use small public fixtures where possible; specify the exact sample-data source and version for every task that needs it.
- Check scene state or output files rather than relying on the model's explanation of what it did.
- Use numeric tolerances for coordinates, measurements, and voxel counts where exact equality is not appropriate.
- Keep each task focused on one main outcome so failures are easy to classify.
