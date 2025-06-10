# Configuration

## Reference Mark Options

The behaviour of reference mark generation can be tuned via the following configuration options or equivalent CLI arguments:

- `tolerance` – distance used when matching an existing mark.
- `min_distance` – minimum distance a mark must maintain from contours and other marks.
- `available_shapes` – list of shapes that will be cycled through when creating new marks.

These correspond to the CLI flags `--mark-tolerance`, `--mark-min-distance` and `--available-shapes` respectively.
