# Features

LayerForge converts 3D models into a series of SVG slice files.  A stability driven algorithm places reference
marks so the slices can be realigned during reassembly.

## Marker Placement Workflow

1. **Candidate selection** – For each contour a set of candidate points is sampled. The
   :class:`ReferenceMarkCalculator` evaluates these points using a geometric
   stability metric (similar to GDOP) that rewards well‑spaced marks.
2. **Inheritance** – Marks from earlier slices are reused where
   possible. Their shape is preserved so that each layer shares a common set of
   identifiers.
3. **Adjustment** – After initial placement the marks are filtered by
   :class:`ReferenceMarkAdjuster` to ensure they do not overlap each other or sit
   too close to the contours.
4. **Shape choice** – A new mark takes the first configured shape (circle,
   square, triangle, arrow by default) that no mark uses yet. Once every shape is
   in use, new marks take the first shape again.

This process results in clear reference markers that maintain alignment between
layers without interfering with the slice geometry.

See [Reference Mark Algorithm](reference_mark_algorithm.md) for a deeper look at
the metric and adjustment steps.

## Planned changes

The marks are meant to be holes that let a person stack the layers in exactly one way. That needs marks chosen per pair of adjacent layers, shapes chosen to fix rotation, and a check before any file is written. See [Alignment requirements](alignment_requirements.md). The behavior above is what the tool does today.
