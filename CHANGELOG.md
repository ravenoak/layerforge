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

- **Breaking:** A new mark takes the shape with the least symmetry among `--available-shapes`
  (`marks.shapes`), not the first shape in the list that no mark uses yet, and the order of the
  list no longer matters. A shape with a direction (the triangle or the arrow) comes before
  the square, and the square before the circle. Of the two with a direction, the larger outline
  wins, so the defaults give a triangle for every mark. Every mark of a run has one angle, so
  one mark with a direction fixes the rotation of its piece (TR-2, TR-8). Measured on a 20 mm
  cube at layer height 5: slice 0 held a circle mark (`<circle ... r="2.5">`) and now holds a
  triangle (`<polygon class="mark" points="2.5,0.0 -1.9151,1.607 -1.9151,-1.607">`) at the
  same point, the centre. The outline is the same, and the number moves from (5.958, -3.183)
  to (5.670, 6.459), because it sits where its box is farthest from the cuts. Two 20 mm cubes
  side by side got a circle and a square in slice 0 and now get two triangles. A 10 mm cube at
  the defaults warned that the number did not fit in all 4 slices (it needed 4.83 mm) and now
  gives no warning. An 8 mm and a 9 mm box still warn in all 4 slices, with hints of 3.75 and
  4.58 mm instead of 3.25 and 4.01. `--available-shapes circle` gives circle marks again. The
  `Slice._select_unique_shape` method is removed; `choose_shape` in
  `layerforge.models.reference_marks.shape_choice` replaces it. The points are still chosen
  with a disc that holds every listed shape, so a shape that is never used still takes room
  (#198). (#61, G-5)
- **Breaking:** The label is the layer number alone (`0`, `1`, ...), not `Slice N`. It is
  `--number-height` tall (5 mm by default), centred, in bold sans-serif, and placed where its
  box is farthest from the outline, the holes and every mark, the kerf away from each. Before,
  it sat at the centroid at 1/20 of the drawing and could cross an outline or a hole. When it
  fits nowhere, it is drawn at the middle of the piece and one warning names the slice.
  Measured at the defaults, a 10 mm cube warns in all 4 slices, since the mark (3 mm) and the
  number (5 mm) do not fit in 10 mm, and 20 mm and 40 mm cubes give no warning. (Measured with
  circle marks; since #61 the default mark is a triangle and the 10 mm cube gives no warning.)
  (#75, G-18)
- **Breaking:** Python API. `SliceSVGDrawer.draw_slice` no longer takes `padding` or
  `font_size`; the number comes from `SVGStyle` (`number_height`, `number_width_factor`,
  `number_clearance`). (#75, #171)
- **Breaking:** The SVG is laser output. Outlines and holes are hairlines of 0.01 mm
  (`output.hairline_width`, in the unit of the run) in the cut colour, red by default, with no
  fill and a `class` of `outline` or `mark`. Before, outlines were black, each mark shape had
  its own colour, and the root set a stroke width of 1/200 of the drawing. The root
  `font-size` and `stroke-width` are gone; the label carries its own `font-size`, with the
  same value, and the `fill` of the engrave colour. `stroke-width` is plain decimal text, so
  0.01 mm with `--units in` is `0.00039370078740157485` and not `0.0004`. (#83, #145, Refs #154)
- **Breaking:** `--mark-color` is removed. Use `--cut-color`. A bad colour now exits with
  code 2 before the prompt and names the option, where it ended in a traceback after the
  slicing. (#83, #145)
- **Breaking:** Python API. The `color` field is removed from `BaseShape`, `ReferenceMark`,
  `ReferenceMarkConfig`, `ReferenceMarkManager.add_or_update_mark` and `Slice`.
  `ReferenceMarkConfig` raises on an unknown field, so `color=` is an error and not dropped.
  A drawing strategy implements `element(dwg, shape)` and returns an unstyled element, where
  it had `draw`. `SVGGenerator` and `draw_slice` take a `style` (`SVGStyle`). (#83)
- **Breaking:** The default mark size, minimum distance and tolerance follow the sheet
  and the kerf, not the model. The size is the larger of the layer height and 1.5 times
  the kerf (3 for the default 3 mm sheet and 0.3 mm kerf), and it no longer depends on
  the distance from the origin. `--mark-min-distance` defaults to the mark size (it was
  10) and `--mark-tolerance` to 0.1 times it (it was 10). Measured on cubes centred on the
  origin at layer height 3: a 10 mm cube goes from 0 marks to 4 in 4 slices, and the
  20 mm and 30 mm cubes keep their 7 and 10 marks, of radius 1.5. At layer height 5 the
  radius of the marks of the 20 mm and 30 mm cubes grows from 1.5 to 2.5, and a 10 mm cube
  still gets none. A run with a config file or options that name a size, a distance or a
  tolerance is not affected. (#62, #76, G-6, G-19)
- **Breaking:** With `--units cm` or `--units in`, the default layer height is 3 mm stated
  in that unit (0.3 cm, 0.118 in), where it was 3.0 in that unit. A layer height that you
  give is not converted. (#62)
- **Breaking:** Python API. `Slice` needs `layer_height` (keyword only). `ReferenceMarkConfig`
  has `size`, `min_distance` and `tolerance` as `None` until they are set or derived, and
  `resolved(layer_height)` derives them; `Slice` and `SlicerService.slice_model` do that.
  `ReferenceMarkAdjuster` and `ReferenceMarkManager` raise `ValueError` for a value that is
  not set. `mark_size_at` and `Slice._calculate_mark_size` are removed. (#62, #165)
- **Breaking:** Every mark shape is a closed outline anchored at its centre, and
  its size is the diameter of the smallest circle around the centre that holds
  it. At size 10 the square's area falls from 100 to 50 (the side is now the
  size divided by √2), and the triangle's from 200 to 28.4 (it was 2 × size wide
  and tall). The arrow is a closed polygon of seven vertices with its tip at
  the size divided by two from the centre. It was a line of the full size from
  its tail, with an open head. Angle 0 now points along +x for every shape. The
  triangle pointed up. In the SVG the square and the arrow are `<polygon>`
  elements, and the arrow no longer has a `<line>`. (#84, G-20)
- **Breaking:** A mark is kept only if its whole hole fits. The hole must lie inside
  the piece, with at least the web of material around it and between two holes.
  The web is half the layer height by default (`marks.min_web_ratio`). Before, only the
  centre was checked, so a large mark could cross an edge or overlap another. A
  20 x 6 x 10 bar with layer height 5, `--mark-size 8` and `--mark-min-distance 2` had
  a circle in each of its 2 files, and now has none and 2 warnings. A 20 mm cube at
  layer height 5 with the defaults writes the same 4 files, byte for byte. The
  warning now reads `Try a smaller --mark-min-distance or --mark-size.` (#85, G-21)
- **Breaking:** `BaseShape` has an abstract `outline()` and a `symmetry_order`. A shape
  registered with `register_shape` must define `outline()`, or it can no longer be created.
  (#84)
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

- The warning that a number does not fit now gives the tallest height that does fit
  (`Try --number-height 4.83 (number.height in the config file)`), or says that no height
  fits. Measured, with circle marks and before #61: the 10 mm cube at the defaults needs
  4.83 mm, not 5, and warns in all 4 slices without it. The warning that no mark fits also names the config keys
  (`marks.min_distance`, `marks.size`) beside the options. `largest_fitting_height` in
  `layerforge.models.slicing.number` finds the height. (#190, #189)
- A warning when `--cut-color` and `--engrave-color` are the same colour (compared as text,
  ignoring case). A laser program gives one operation to a colour, so the number and the
  outlines would share it. (#180)
- `adjacent_pairs` in `layerforge.models.slicing.adjacency` (Python API). For each two adjacent
  layers it returns the pairs of overlapping pieces, each with its overlap and the overlap moved
  in by a clearance. Nothing in the command uses it yet. (#89)
- `rotation_symmetry` in `layerforge.models.reference_marks` (Python API). Given marks and a
  tolerance, it returns the turns other than none that map the marks onto themselves, each mark
  keeping its shape, size and angle (TR-2). A circle alone, or several circles in one place,
  has unlimited symmetry. It raises `ValueError` for a tolerance that is not positive and
  finite. A mark listed twice counts once. Nothing in the command uses it yet. (#90)
- `--number-height` and the config-file table `[number]` with `height` and `width_factor`.
  `place_number` in `layerforge.models.slicing.number` returns where the number of a piece
  goes. (#75)
- `--cut-color` and `--engrave-color` (default red and black), and the config-file table
  `[output]` with `cut_color`, `engrave_color` and `hairline_width`. A colour is a name, `#rgb`,
  `#rrggbb` or `rgb(r,g,b)`. (#83)
- `--kerf` and the `kerf` key: the width of material the tool removes, default 0.3 mm
  stated in `--units`. The keys `marks.min_hole_ratio` (1) and `marks.min_hole_kerf_factor`
  (1.5) give the least hole size, with no command-line option. A `--mark-size` below that
  size logs one warning for the run, and the run goes on. (#62, TR-6)
- `marks.min_web_ratio` in the config file: the least material between two holes, and
  between a hole and an outline, as a multiple of the layer height. Default 0.5.
  It has no command-line option. (#85)
- Python API: `ReferenceMarkAdjuster.adjust_marks` takes a keyword `min_web`, `Slice` takes
  `layer_height`, and `layerforge.models.reference_marks` exports `mark_footprint`. The shape registry lives in `layerforge.domain.shapes.registry`;
  `layerforge.svg.drawing.shape_factory` still exports the same names. (#85)
- `--units` (`mm`, `cm` or `in`, default `mm`) and the `units` key of the config file.
  An STL file has no unit, so the option states the unit of the model and of every
  length option, and labels the size of each SVG. A length that you give is not
  converted. The defaults for the layer height and the kerf are stated in the unit (#62).
  (#74, G-17)
- A TOML config file. `--config PATH` names it, and `layerforge.toml` in the
  current directory is read when it exists, so **a `layerforge.toml` you already
  have there now changes the run**. Keys: `layer_height`, and `size`,
  `tolerance`, `min_distance`, `shapes` and `angle` under `[marks]`. A value
  from the command line beats the file, and the file beats the default. An
  unknown key or a bad value exits with code 2 and names the file and the key.
  (#87, G-24)
- `--mark-size` sets the size of every new mark. Without it the size follows the
  sheet (see #62 under Changed). (#87)
- One warning per slice when a contour gets no mark. (#70, G-13)

### Fixed

- `--help` no longer sends the reader to `docs/reference_mark_algorithm.md`, a path a
  `pip` or `uv tool install` install does not have. The four mark options lost that
  sentence, and the help ends with one link to the published page. A test checks that
  no help line and no message in `src` names a path of the repository. (#178)
- An error raised while the calculator tests a candidate point no longer reads as
  "outside the piece". The broad `except Exception` around it is removed, so a failure in
  shapely reaches the caller and does not hide as "no mark fits". On a stub that raised
  from its second `contains` call, the old code returned the centroid after 40 swallowed
  errors. A bow-tie, a polygon with no area and an empty polygon give no error. (#171)
- The warning about a mark size below the least hole size no longer ends its sentence
  with the internal requirement ID `(TR-6)`. A test now checks that no string in the
  command's code, and no line of `--help`, names a TR, FR or G number. (#175)
- A slice and its mark store now snap with the same tolerance. When they differed (a
  hand-built `Slice` and manager), a new mark could overwrite a stored mark of another
  shape 30 units away and leave the new position unstored. The slice's tolerance now
  decides both steps, and `ReferenceMarkManager.add_or_update_mark` takes a `tolerance`
  keyword. The command gives both the same value. Its output was identical before and
  after on a 30 mm cylinder and a 30 mm cube at layer height 3 (#108).

- `Slice.adjust_marks` no longer catches the `ValueError` for a mark whose shape name is
  not registered. It used to log one line and keep every mark of the slice unchecked,
  including a circle whose hole crossed the outline. A Python caller now gets the error
  and the marks stay as they were. The command is not affected, because it checks the
  shape names first (FR-6). The `except` dated from the first commit and guarded a
  function that no longer exists (#162).

- The command no longer chooses a point for a circle mark that the check after it drops.
  The point was chosen with a disc of radius size / 2, and the circle's checked outline
  reaches 0.12% further (5.00603 at size 10). On a square piece 6.0 or 6.002 wide (size 3,
  web 1.5) the calculator chose the centre and the check dropped it. The disc now has the reach of the farthest available shape. The
  checks keep the polygon of the circle, not the exact circle, so a circle that passes
  never crosses an edge (#157). A Python caller whose `available_shapes` names an
  unregistered shape now gets a `ValueError` from the calculator. Before, it got a
  mark. The command is not affected, because it checks the names first (FR-6).

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
- An `--output-folder` that is empty or blank, that cannot be written (or would have to be
  made in a folder that cannot be written), or whose name the system refuses (over 255
  characters), exits with code 2 and names the option, before the `--stl-file` prompt.
  They ended in a traceback after the slicing, and an empty one pointed at the
  filesystem root. The check makes no folder. (#149, G-31)
- `--help` shows the help and exits with code 0 when the config file is bad, and
  `--config FILE --help` no longer prints `Using settings from FILE`. The first
  case exited with code 2. (#136)

### Removed

- **Breaking:** Python API. `Model.origin`, `Slice.origin` and the `origin` argument of
  `Model(...)` and `Slice(...)` are removed, with `ModelFactory._calculate_origin`.
  Nothing read them since the mark size stopped depending on the place (#170). A call that
  passes `origin` now raises `TypeError`. The command's output does not change. (#172)
- `Model.calculate_height`. Nothing used it. (#78)
- `Triangle.vertices`. Use `Triangle.outline()`, a shapely polygon. (#84)

[Unreleased]: https://github.com/ravenoak/layerforge/commits/main
