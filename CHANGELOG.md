# Changelog

All notable changes to LayerForge are listed here. The format follows
[Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/).

## Version policy

LayerForge is at 0.x, so a minor version (0.1 to 0.2) may break the command line,
the output files or the Python API. A patch version (0.1.0 to 0.1.1) only fixes
bugs. From 1.0.0 the project follows [Semantic Versioning](https://semver.org/).

Every pull request that changes what a user sees adds a line under `Unreleased`.
That covers options, defaults, exit codes, output files and public functions. Mark
a line **Breaking** when existing use stops working or gives different output.

The version in `pyproject.toml` is 0.1.0, and no release has been tagged or
published. All changes since then are under `Unreleased`. Because they change the
output, the first release will raise the minor version.

## [Unreleased]

### Changed

- **Breaking:** Every mark shape is a closed outline anchored at its centre, and
  its size is the diameter of the smallest circle around the centre that holds
  it. At size 10 the square's area falls from 100 to 50 (the side is now the
  size divided by √2), and the triangle's from 200 to 28.4 (it was 2 × size wide
  and tall). The arrow is a closed polygon of seven vertices with its tip at
  the size divided by two from the centre. It was a line of the full size from
  its tail, with an open head. Angle 0 now points along +x for every shape. The
  triangle pointed up. In the SVG the square and the arrow are `<polygon>`
  elements, and the arrow no longer has a `<line>`. (#84, G-20)
- **Breaking:** Slices are cut at the middle of each layer, counted from the
  mesh's lowest z, not from z = 0. A mesh 10 high with layer height 3 was cut at
  0, 3, 6, 9 and 10, and is now cut at 1.5, 4.5, 7.5 and 9.5. The number of
  slices can change, so the file names can too. (#70, G-1, G-10)
- **Breaking:** The y axis of every SVG is flipped, so a slice is no longer
  mirrored. Each SVG has one shared `viewBox`, and the root font size and stroke
  width scale with it. (#70, G-12)
- **Breaking:** All slices share the model's x and y frame. Before, each cut was
  re-centred on its own vertices, so marks did not line up between slices.
  (#70, G-2)
- **Breaking:** `SlicerService.calculate_slice_positions` takes
  `(bottom, top, layer_height)`. It took `(total_height, layer_height)`. (#70)
- **Breaking:** Angles are radians everywhere in the Python package, and the
  arrow's degree heuristic is gone. The `--mark-angle` option is still in
  degrees. (#70, G-8)
- A missing, unreadable or empty mesh file, a mesh with no height and an
  unknown or empty `--available-shapes` now stop the command with a message that
  names the file or option, before any output is written. (#70, G-11)
- Candidate points are sampled with a fixed seed, so the same model gives the
  same marks on every run. (#70, G-9)
- A shared mark is now one mark. A point within `--mark-tolerance` of a stored
  mark takes its coordinates, and the nearest stored mark wins. A new mark is
  no longer placed within the tolerance of a stored mark. A slice that cannot
  reuse a stored mark, and has no room outside its tolerance, may now get no
  mark, with the usual warning, where it used to get a mark at a drifting
  position.
  (#72, #82, G-15, G-22)
- The command prints `Using settings from <file>` to stderr when it reads a
  config file, from `--config` or from `layerforge.toml` in the current
  directory. Before, a stray file changed a run in silence. (#118, G-26)
- A wrong type (`--layer-height abc`) or a `--config` path that does not exist is
  reported before a bad config file, whichever is typed first. Both exit with
  code 2. (#136)
- `process_model` reports a bad config file before the scale and target conflict,
  as the command does. It reported the conflict first. The command's behavior is
  the same. (#136)
- **Breaking:** Every SVG has a physical size. The root `width` and `height` were
  `100%`. They are now the `viewBox` width and height with a unit (`mm` unless
  `--units` says otherwise), for example `33.0cm`. A laser program or a printer
  now reads the size from the file, and every layer has the same size. The
  numbers in the file do not change. (#74, G-17)

### Added

- `--units` (`mm`, `cm` or `in`, default `mm`) and the `units` key of the config file.
  An STL file has no unit, so the option states the unit of the model and of every
  length option, and labels the size of each SVG. Nothing is converted. With
  `--units in`, the default mark distances of 10 are 10 inches. (#74, G-17)
- A TOML config file. `--config PATH` names it, and `layerforge.toml` in the
  current directory is read when it exists, so **a `layerforge.toml` you already
  have there now changes the run**. Keys: `layer_height`, and `size`,
  `tolerance`, `min_distance`, `shapes` and `angle` under `[marks]`. A value
  from the command line beats the file, and the file beats the default. An
  unknown key or a bad value exits with code 2 and names the file and the key.
  (#87, G-24)
- `--mark-size` sets the size of every new mark. Without it the size is still
  3 to 5, by distance from the model origin. (#87)
- One warning per slice when a contour gets no mark. (#70, G-13)

### Fixed

- Loops inside a contour become holes in the slice. Marks avoid the holes, and
  the SVG outlines them. (#70, G-3)
- A negative `--mark-tolerance` or `--mark-min-distance` exits with code 2 and
  names the option. It ended in a traceback. (#71, G-14)
- `nan` and `inf` for `--layer-height`, `--scale-factor`, `--target-height`,
  `--mark-tolerance`, `--mark-min-distance` and `--mark-angle` exit with code 2
  and name the option. Before, most ended in a traceback, and the rest ran
  with a meaningless value. `ReferenceMarkConfig` rejects them too. (#106)
- `--scale-factor` with `--target-height` exits with code 1 and the conflict
  message for every value. `--scale-factor 0` used to count as not given and
  exited with code 2. (#117, G-25)
- A bad config file (`layerforge.toml` or `--config`) is reported before the
  command asks for `--stl-file`, and before an option conflict. It was reported
  after the person typed the path. (#119, G-27)
- Every bad option value, and `--scale-factor` with `--target-height`, is reported
  before the command asks for `--stl-file`. The exit codes are the same as before
  (2 for a bad value, 1 for the conflict). The person used to type the path
  first. (#135, G-28)
- An `--output-folder` that is a file, a dangling symlink, or lies inside a file,
  exits with code 2 and names the option. It ended in a traceback after the slicing.
  (#144, G-29)
- `--help` shows the help and exits with code 0 when the config file is bad, and
  `--config FILE --help` no longer prints `Using settings from FILE`. The first
  case exited with code 2. (#136)

### Removed

- `Model.calculate_height`. Nothing used it. (#78)
- `Triangle.vertices`. Use `Triangle.outline()`, a shapely polygon. (#84)

[Unreleased]: https://github.com/ravenoak/layerforge/commits/main
