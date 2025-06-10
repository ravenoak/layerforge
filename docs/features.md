# Features

LayerForge converts 3D models into a series of SVG slice files.  A stability driven algorithm places reference
marks so the slices can be realigned during reassembly.

## Marker Placement Workflow

1. **Candidate selection** – For each contour a set of candidate points is sampled. The
   :class:`ReferenceMarkCalculator` evaluates these points using a geometric
   stability metric (similar to GDOP) that rewards well‑spaced marks.
2. **Inheritance** – Existing marks from neighbouring slices are reused where
   possible. Their shape is preserved so that each layer shares a common set of
   identifiers.
3. **Adjustment** – After initial placement the marks are filtered by
   :class:`ReferenceMarkAdjuster` to ensure they do not overlap each other or sit
   too close to the contours.
4. **Shape cycling** – New marks cycle through the configured list of shapes
   (circle, square, triangle, arrow by default) so each new marker is easy to
   identify.

This process results in clear reference markers that maintain alignment between
layers without interfering with the slice geometry.

