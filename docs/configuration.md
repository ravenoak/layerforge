# Configuration

## Output colours

Outlines and holes are cut lines. They are drawn as hairlines in `--cut-color` (default red), with no fill and a `class` of `outline` or `mark`. The number is engraved, in `--engrave-color` (default black). A colour is any SVG colour: a name such as `red`, a hex value such as `#f00`, or `rgb(255,0,0)`. A bad colour stops the run with exit code 2, before the prompt. Laser programs pick the operation by colour, so set these to the colours your program maps to cut and engrave.

## Reference Mark Options

The behaviour of reference mark generation can be tuned via the following
configuration options or the equivalent CLI arguments:

- `tolerance` – distance used when matching an existing mark. Without it, 0.1 times the mark size.
- `min_distance` – minimum distance a mark must maintain from contours and other marks. Without it, the mark size.
- `available_shapes` – list of shapes for new marks. A new mark takes the first shape not yet in use.
- `angle` – default orientation angle for generated marks. The CLI flag takes
  degrees; `ReferenceMarkConfig.angle` is in radians.
- `size` – size of every new mark. Without it the size is the larger of `min_hole_ratio` times the layer height (the sheet thickness) and `min_hole_kerf_factor` times the kerf. It does not depend on where the mark lies or on the size of the model. A size below that minimum is a warning, not an error.
- `kerf` – the width of material the tool removes. It is a top-level key (`--kerf`), not a mark option. Use 0 for a CNC router or hand work.
- `min_hole_ratio` and `min_hole_kerf_factor` – the two factors of the default size. They are keys of the config file only, in `[marks]`, with no command-line flag.
- `min_web_ratio` – the least material between two holes, and between a hole and an outline, as a multiple of the layer height. It is a key of the config file only, `[marks]` `min_web_ratio`, with no command-line flag.

These correspond to the CLI flags `--mark-tolerance`, `--mark-min-distance`,
`--available-shapes`, `--mark-angle` and `--mark-size` respectively, and `--kerf`
for the kerf.

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
kerf = 0.3                # the width of material the tool removes

[marks]
size = 3.0                # size of every new mark
tolerance = 0.3
min_distance = 6.0
shapes = ["circle", "triangle", "square"]
angle = 0                 # degrees

[output]
cut_color = "red"         # outlines and holes
engrave_color = "black"   # the number
hairline_width = 0.01     # stroke width of a cut line, in the unit above
```

Every key is optional. A value from the command line beats the file, and the file
beats the default.

| Key | Option | Default |
|---|---|---|
| `units` | `--units` | `"mm"` |
| `layer_height` | `--layer-height` | `3.0` |
| `kerf` | `--kerf` | `0.3` |
| `marks.size` | `--mark-size` | none: the larger of `min_hole_ratio` × layer height and `min_hole_kerf_factor` × kerf |
| `marks.tolerance` | `--mark-tolerance` | none: 0.1 × the mark size |
| `marks.min_distance` | `--mark-min-distance` | none: the mark size |
| `marks.shapes` | `--available-shapes` | `["circle", "square", "triangle", "arrow"]` |
| `marks.angle` | `--mark-angle` | `0.0` |
| `marks.min_web_ratio` | none | `0.5` |
| `marks.min_hole_ratio` | none | `1.0` |
| `marks.min_hole_kerf_factor` | none | `1.5` |
| `output.cut_color` | `--cut-color` | `"red"` |
| `output.engrave_color` | `--engrave-color` | `"black"` |
| `output.hairline_width` | none | `0.01` |

The defaults of `layer_height` (3 mm), `kerf` (0.3 mm) and `output.hairline_width` (0.01 mm) are millimetres. With `--units cm` or
`--units in` they are stated in that unit: 3 mm is 0.3 cm or 0.118 in. A value that you give, in the
file or on the command line, is already in the units and is not converted. The three mark numbers
with no default number (size, tolerance and minimum distance) are worked out from the sheet, so they follow `--units` too.

`--scale-factor`, `--target-height`, `--stl-file` and
`--output-folder` are not settings and have no key.

An unknown key, a value of the wrong type, and a number that is not finite or out
of range stop the run before the command asks for the STL file. The exit code is 2 and the message
names the file and the key, for example
`layerforge.toml: marks.tolerance: must be >= 0`. A bad file value fails even when
an option overrides it. A bad option value names the option.

## Planned options

The target adds more settings to the file, each with its own key: `--number-height` and `--allow-unaligned`. See [Alignment requirements](alignment_requirements.md#settings).
