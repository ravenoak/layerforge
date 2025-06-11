# Reference Mark Algorithm

This page details how LayerForge selects and refines alignment marks for each
slice. The algorithm is based on a geometric stability metric inspired by GDOP
(Geometric Dilution of Precision). It ensures marks remain consistent between
layers while avoiding overlaps.

## Candidate Scoring

For each contour a set of candidate points is sampled. The
`ReferenceMarkCalculator` computes a **stability score** equal to the total
pairwise distance between the points. Higher scores mean the marks are farther
apart and thus easier to align.

```python
class ReferenceMarkCalculator:
    @staticmethod
    def _stability_score(points: list[tuple[float, float]]) -> float:
        score = 0.0
        for i, p1 in enumerate(points):
            for p2 in points[i + 1:]:
                score += calculate_distance(p1[0], p1[1], p2[0], p2[1])
        return score
```

Marks are chosen iteratively. Existing marks from neighbouring layers are tried
first; otherwise the best scoring candidate is selected.

## Inheriting Marks

When processing a slice, the algorithm checks whether any stored mark lies inside
a contour at a safe distance from the edges. If so, that mark is reused and keeps
its original shape **as well as its orientation angle and stroke color**. This
inheritance gives each layer a shared set of identifiers for accurate reassembly.

```mermaid
flowchart TD
    A[Previous slice marks] --> B{Inside polygon?}
    B -- yes --> C[Reuse mark]
    B -- no --> D[Evaluate candidates]
```

## Adjusting Marks

After placement, marks may still be too close to a contour or to one another.
`ReferenceMarkAdjuster` filters marks that violate the configured minimum
separation:

```python
class ReferenceMarkAdjuster:
    @staticmethod
    def adjust_marks(marks, contours, config=None):
        adjusted = []
        for mark in marks:
            pt = Point(mark.x, mark.y)
            if any(poly.boundary.distance(pt) < config.min_distance for poly in contours):
                continue
            if any(pt.distance(Point(m.x, m.y)) < config.min_distance for m in adjusted):
                continue
            adjusted.append(mark)
        return adjusted
```

The final mark set thus respects minimum distances while preserving inherited
shapes whenever possible.

## Parameter Effects

The parameters controlling mark placement can be tuned to suit different model
sizes. The following diagrams illustrate how each option influences the final
reference marks.

### `tolerance`

Marks from a previous slice are reused when they fall within the tolerance
radius of a candidate position.

```mermaid
flowchart LR
    A((Stored mark)) -- within tolerance --> B[Reuse]
    A -- beyond tolerance --> C[New mark]
```

### `min_distance`

Marks must stay at least this far from contours **and** other marks.

```mermaid
flowchart LR
    C[Contour]
    M1((Mark1)) -- min_distance --> C
    M1 ---|min_distance| M2((Mark2))
```

### `available_shapes`

When a new mark is required the shapes are cycled in order.

```mermaid
flowchart LR
    S1[Circle] --> S2[Square] --> S3[Triangle] --> S4[Arrow] --> S1
```

### `angle`

Controls the orientation of newly generated marks.

```mermaid
flowchart LR
    A[Default orientation] -- angle --> B[Rotated]
```

### `color`

Sets the stroke color used when drawing marks. It does not affect placement but
may improve visibility in the output SVGs.

#### Tips for Different Model Scales

- **Small models (<10&nbsp;cm)** – use a `min_distance` around 2&ndash;5 units and
  a lower `tolerance` to prevent clutter.
- **Medium models (10&ndash;30&nbsp;cm)** – the defaults (10 units) usually work
  well.
- **Large models (>30&nbsp;cm)** – increase both `min_distance` and `tolerance`
  proportionally (15&ndash;25 units) so marks remain distinct.

