Synthetic benchmark fixtures

- benchmark_ct.nrrd: 48x48x32 short CT-like phantom, 1 mm isotropic; intensity bands at -1000, 50, 600, and 1200 HU.
- MRHead.nrrd and brain.nii.gz: existing MRI volume fixtures.
- dicom_series/: three-slice explicit-VR CT series (description: Synthetic Test CT).
- islands.seg.nrrd: one TumorMask segment with one large component and three isolated voxels.
- labelmap.nrrd: unsigned-char labelmap with labels 1 and 2.
- sphere_model.stl: small closed triangulated sphere surface.
- fiducials.mrk.json: three RAS fiducials.
- outputs/: destination for generated benchmark results.
