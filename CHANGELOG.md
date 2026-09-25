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

### Added

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

### Removed

- `Model.calculate_height`. Nothing used it. (#78)

[Unreleased]: https://github.com/ravenoak/layerforge/commits/main
