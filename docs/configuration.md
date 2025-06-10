# Configuration

## Reference Mark Options

The behaviour of reference mark generation can be tuned via the following
configuration options or the equivalent CLI arguments:

- `tolerance` – distance used when matching an existing mark.
- `min_distance` – minimum distance a mark must maintain from contours and other marks.
- `available_shapes` – list of shapes that will be cycled through when creating new marks.

These correspond to the CLI flags `--mark-tolerance`, `--mark-min-distance` and
`--available-shapes` respectively.

### Workflow

1. Candidate points are sampled within each contour and ranked using the
   stability metric implemented in ``ReferenceMarkCalculator``.
2. Marks inherited from neighbouring slices keep their original shape so layers
   remain easy to align.
3. Newly created marks cycle through ``available_shapes`` and are filtered by
   ``ReferenceMarkAdjuster`` to ensure a minimum distance from contours and other
   marks.

By adjusting ``tolerance`` and ``min_distance`` you can control how closely marks
match between slices and how near they may appear to each other.
