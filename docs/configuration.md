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
- `size` – size of every new mark. Without it the size follows the distance from the model origin.

These correspond to the CLI flags `--mark-tolerance`, `--mark-min-distance`,
`--available-shapes`, `--mark-angle`, `--mark-color` and `--mark-size` respectively.

### Workflow

1. Candidate points are sampled within each contour and ranked using the
   stability metric implemented in ``ReferenceMarkCalculator``.
2. Marks inherited from earlier slices keep their original position and shape so layers
   remain easy to align.
3. Newly created marks take the first unused shape from ``available_shapes`` and are filtered by
   ``ReferenceMarkAdjuster`` to ensure a minimum distance from contours and other
   marks.

By adjusting ``tolerance`` and ``min_distance`` you can control how closely marks
match between slices and how near they may appear to each other.

## Config file

A TOML file can hold the settings you use on every run, such as your sheet
thickness. Use `--config PATH`, or save it as `layerforge.toml` in the directory
you run the command from. A `layerforge.toml` there is read on every run, so it
changes the result. The command prints `Using settings from <file>` to stderr
when it uses a file.

```toml
units = "mm"              # the unit of the model and of every length: mm, cm or in
layer_height = 3.0        # the sheet thickness

[marks]
size = 3.0                # size of every new mark
tolerance = 5.0
min_distance = 6.0
shapes = ["circle", "triangle", "square"]
angle = 0                 # degrees
```

Every key is optional. A value from the command line beats the file, and the file
beats the default.

| Key | Option | Default |
|---|---|---|
| `units` | `--units` | `"mm"` |
| `layer_height` | `--layer-height` | `3.0` |
| `marks.size` | `--mark-size` | none: 3 to 5, by distance from the model origin |
| `marks.tolerance` | `--mark-tolerance` | `10.0` |
| `marks.min_distance` | `--mark-min-distance` | `10.0` |
| `marks.shapes` | `--available-shapes` | `["circle", "square", "triangle", "arrow"]` |
| `marks.angle` | `--mark-angle` | `0.0` |

`--mark-color`, `--scale-factor`, `--target-height`, `--stl-file` and
`--output-folder` are not settings and have no key.

An unknown key, a value of the wrong type, and a number that is not finite or out
of range stop the run before the command asks for the STL file. The exit code is 2 and the message
names the file and the key, for example
`layerforge.toml: marks.tolerance: must be >= 0`. A bad file value fails even when
an option overrides it. A bad option value names the option.

## Planned options

The target adds more settings to the file, each with its own key: `--kerf`, `--number-height`, `--allow-unaligned`, `--cut-color` and `--engrave-color`. It changes the defaults and meaning of `--mark-min-distance` and `--mark-tolerance`, sets the default mark size from the sheet thickness, and removes `--mark-color`. See [Alignment requirements](alignment_requirements.md#settings).
