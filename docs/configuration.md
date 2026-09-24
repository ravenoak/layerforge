# Configuration

## Reference Mark Options

The behaviour of reference mark generation can be tuned via the following
configuration options or the equivalent CLI arguments:

- `tolerance` – distance used when matching an existing mark.
- `min_distance` – minimum distance a mark must maintain from contours and other marks.
- `available_shapes` – list of shapes for new marks. A new mark takes the first shape not yet in use.
- `angle` – default orientation angle for generated marks. The CLI flag takes
  degrees; `ReferenceMarkConfig.angle` is in radians.
- `color` – outline color used when drawing marks.

These correspond to the CLI flags `--mark-tolerance`, `--mark-min-distance`,
`--available-shapes`, `--mark-angle` and `--mark-color` respectively.

### Workflow

1. Candidate points are sampled within each contour and ranked using the
   stability metric implemented in ``ReferenceMarkCalculator``.
2. Marks inherited from earlier slices keep their original shape so layers
   remain easy to align.
3. Newly created marks take the first unused shape from ``available_shapes`` and are filtered by
   ``ReferenceMarkAdjuster`` to ensure a minimum distance from contours and other
   marks.

By adjusting ``tolerance`` and ``min_distance`` you can control how closely marks
match between slices and how near they may appear to each other.

## Planned options

The target adds `--units`, `--mark-size`, `--number-height`, `--allow-unaligned`, `--cut-color` and `--engrave-color`. It changes the defaults and meaning of `--mark-min-distance` and `--mark-tolerance`, and removes `--mark-color`. See [Alignment requirements](alignment_requirements.md#command-line-changes).
