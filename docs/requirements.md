# Requirements

This page lists what LayerForge does today, derived from the code and tests as of 2026-09. It describes current behavior, not intended behavior. Where the two differ, the difference is listed under [Known gaps](#known-gaps). The intended behavior for alignment, which the tool does not yet meet, is on the [Alignment requirements](alignment_requirements.md) page.

The same behavior is written as a formal specification in [`specs/layerforge.allium`](https://github.com/ravenoak/layerforge/blob/main/specs/layerforge.allium). The rule names there match the IDs here.

## Purpose

LayerForge slices a 3D mesh into horizontal layers. It writes one SVG file per layer. Each SVG has the layer outline, numbered reference marks, and a slice number. A person cuts the layers, stacks them, and uses the marks to align them. The marks are meant to be holes cut through the sheet, and the layers must be alignable in exactly one way. The tool does not check that yet (see G-4).

## How to read this page

- **FR** is a functional requirement. **NFR** is a non-functional requirement. **C** is a constraint.
- **Code** names the module and symbol (`path::symbol`). Line numbers are left out because they drift.
- **Tests** names the test files that cover the requirement. A dash means no test covers it directly.
- Paths are relative to `src/layerforge/` for code and `tests/` for tests.

## Functional requirements

### Command line

| ID | Requirement | Code | Tests |
|---|---|---|---|
| FR-1 | The `layerforge` command takes `--stl-file`. If it is missing, the command prompts for it, after the config file and every option have been checked (FR-30, NFR-5), so a bad option never leaves the person typing a path first. | `cli.py::cli` | `test_cli`, `test_cli_checks_before_prompt` |
| FR-2 | `--layer-height` is a number greater than 0. The default is 3.0, or the `layer_height` key of the config file (FR-30). A value of 0 or less stops the command with `Invalid value for --layer-height: must be > 0` and exit code 2. So does `nan` or `inf`, with `must be a finite number`. The check runs before the `--stl-file` prompt. | `cli.py::resolve_settings` | `test_process_model_validation`, `test_cli`, `test_cli_checks_before_prompt`, `test_settings` |
| FR-3 | `--scale-factor` and `--target-height`, when given, must be greater than 0. Both fail the same way as FR-2, and `nan` or `inf` fails too. The check runs before the `--stl-file` prompt. | `cli.py::resolve_settings` | `test_process_model_validation`, `test_cli_checks_before_prompt` |
| FR-4 | `--scale-factor` and `--target-height` cannot be used together. The command prints `Only one of scale_factor or target_height can be provided.` and exits with code 1, whatever the values are. The conflict is reported before a bad value (FR-2, FR-3), after a bad config file (FR-30), and before the `--stl-file` prompt. `process_model` checks in the same order as the command. | `cli.py::resolve_settings`, `cli.py::cli` | `test_cli`, `test_cli_checks_before_prompt` |
| FR-5 | `--output-folder` sets where SVG files go. The default is `output`. The folder and its parents are created if missing. A folder that is an existing file, or that would have to be made inside one, stops the command with `Invalid value for --output-folder: <file> is not a folder` and exit code 2, before the `--stl-file` prompt. `<file>` is the existing path in the way, which for a folder inside a file is the file, not the path that was typed. A dangling symlink counts. | `utils/file_operations.py`, `writers/svg_writer.py`, `cli.py::_check_output_folder` | `test_file_operations`, `test_end_to_end`, `test_cli_checks_before_prompt` |
| FR-6 | Mark options: `--mark-size` (default none, which keeps the FR-21 rule; a number greater than 0), `--mark-tolerance` (default 10.0), `--mark-min-distance` (default 10.0), `--available-shapes` (comma-separated, default `circle,square,triangle,arrow`), `--mark-angle` (degrees, default 0.0), `--mark-color` (default none). The numbers must be finite. `--mark-size` must be greater than 0, and `--mark-tolerance` and `--mark-min-distance` must not be negative. Shape names are trimmed and empty items dropped. The angle is converted to radians. Each of these except `--mark-color` can also come from the config file (FR-30). The checks run before the `--stl-file` prompt. | `cli.py::resolve_settings` | `test_cli`, `test_cli_checks_before_prompt` |
| FR-30 | A setting comes from the command line first, then a TOML config file, then its default. The file is `--config PATH`, or `layerforge.toml` in the current directory if it exists. Keys: `units`, `layer_height`, and in the `[marks]` table `size`, `tolerance`, `min_distance`, `shapes` (a list) and `angle` (degrees). The options `--mark-color`, `--scale-factor`, `--target-height`, `--stl-file` and `--output-folder` are not settings. An unknown key, a wrong type, or a value that is not finite or out of range (FR-2, FR-6) stops the command with exit code 2 and `<file>: <key>: <reason>`. When a file is used, the command prints `Using settings from <file>` to stderr once, so a stray `layerforge.toml` cannot change a run in silence. The file is read once. It is checked before the `--stl-file` prompt and before the value checks of the other options, so a bad file is reported before an option conflict (FR-4) or a bad option value. click's own errors come first, whatever order the options are typed: an unknown option, a wrong type such as `--layer-height abc`, a missing value, a `--config` path that does not exist. They also exit with code 2. `--help` shows the help and exits with code 0 even when the file is bad, in either order, and prints no `Using settings` line. It still loses to a click error: `--help --bogus` exits with code 2. A bad file value fails even when an option overrides it. A bad option value names the option instead. | `cli.py::_read_settings_file`, `cli.py::resolve_settings`, `settings.py::read_config_file`, `settings.py::merge_settings` | `test_settings`, `test_cli`, `test_cli_checks_before_prompt` |
| FR-31 | `--units` is `mm`, `cm` or `in`. The default is `mm`, or the `units` key of the config file (FR-30). It states the unit of the mesh and of every length option, and it sets the unit of each SVG's `width` and `height` (FR-26). An STL file has no unit, so nothing is converted: with `--units in`, a model 30 across is 30 inches, and so are the mark defaults of FR-6. Any other value stops the command with `Invalid value for '--units': 'ft' is not one of 'mm', 'cm', 'in'.` and exit code 2, before the `--stl-file` prompt. | `cli.py::cli`, `settings.py::Settings`, `svg/svg_generator.py` | `test_cli_checks_before_prompt`, `test_settings`, `test_end_to_end`, `test_svg_output` |

### Loading and scaling

| ID | Requirement | Code | Tests |
|---|---|---|---|
| FR-7 | The mesh is read with trimesh. A file that holds more than one geometry, no geometry, or a mesh with no height is rejected with a `ValueError`. The command turns it into `Cannot load '<file>': <reason>` with exit code 1. A missing or unreadable file fails the same way. | `models/loading/implementations/trimesh_loader.py`, `models/model_factory.py` | `test_trimesh_loader`, `test_model_factory`, `test_process_model_validation` |
| FR-8 | With `--scale-factor`, the mesh is scaled uniformly by that factor about the coordinate origin. | `models/model_factory.py::_scale_mesh` | `test_model_factory`, `test_end_to_end` |
| FR-9 | With `--target-height`, the mesh is scaled uniformly so its height (maximum z minus minimum z) equals the target. | `models/model_factory.py::_scale_mesh` | `test_model_factory`, `test_end_to_end` |
| FR-10 | The model origin is the centre of the mesh bounding box in x and y, taken after scaling. The mesh is not moved. | `models/model_factory.py::_calculate_origin` | `test_model_factory` |

### Slicing

| ID | Requirement | Code | Tests |
|---|---|---|---|
| FR-11 | The model height is maximum z minus minimum z of the mesh bounds. A mesh with no height is rejected when the model is created (NFR-5). | `models/slicing/slicer_service.py::slice_model`, `models/model_factory.py::create_model` | `test_slicer_service`, `test_process_model_validation` |
| FR-12 | The mesh is divided from its lowest point upwards into layers of `layer_height`. The last layer is shorter if the height is not a multiple. There are `ceil(height / layer_height)` layers, at least one. Each slice is cut at the middle of its layer, so no cut lies on the bottom or top face. A mesh 10 high from z = 0 with layer height 3 gives the positions 1.5, 4.5, 7.5 and 9.5. A mesh centred on z = 0 is sliced over its whole height. | `models/slicing/slicer_service.py::calculate_slice_positions` | `test_slicer_service`, `test_end_to_end` |
| FR-13 | Each position is a horizontal plane (normal +z). The cut through the mesh gives closed loops. The loops are combined by the even-odd rule: a loop inside another is a hole, and a loop inside that hole is solid again. Each polygon is in the model's x and y coordinates, so every slice shares one frame. A plane that cuts nothing gives an empty list of polygons. | `models/model.py::calculate_slice_contours` | `test_model_contours`, `test_end_to_end` |
| FR-14 | One slice is made per position, in order and numbered from 0. Empty slices are kept. | `models/slicing/slicer_service.py::slice_model` | `test_end_to_end` |

### Reference marks

| ID | Requirement | Code | Tests |
|---|---|---|---|
| FR-15 | Each polygon gets at most one mark. | `models/reference_marks/reference_mark_calculator.py::get_stable_marks` | `test_reference_mark_calculator`, `test_reference_mark_property` |
| FR-16 | Candidate points for a polygon are its centroid, if the centroid is inside the polygon, plus random points inside its bounding box that fall inside the polygon (up to 40 tries, 4 wanted). The random generator has a fixed seed, so the same polygon always gives the same points. | `models/reference_marks/reference_mark_calculator.py::_sample_points` | `test_calculator_get_potential_marks` |
| FR-17 | A point qualifies only if it is at least `min_distance` from the polygon boundary and from marks already chosen in the same slice. A sampled point must also lie farther than `tolerance` from every stored mark and every mark already chosen, because a point in that range would be taken for that mark (FR-19). | same | `test_reference_mark_property` |
| FR-18 | An earlier mark that qualifies and lies inside the polygon is reused. Otherwise the qualifying candidate with the highest stability score wins. The score is the sum of distances between all pairs of points, the candidate and the marks already chosen. | same | `test_calculator_get_potential_marks`, `test_reference_mark_property` |
| FR-19 | Marks are shared across all slices in one run. A chosen point that lies within `tolerance` of an earlier mark is that mark: it takes the stored coordinates, shape, size, angle and color. When several stored marks are in range, the nearest wins, and the earliest of equally near ones. | `models/slicing/slice.py::process_reference_marks`, `models/reference_marks/reference_mark_manager.py` | `test_slice_mark_inheritance`, `test_slice_process_reference_marks`, `test_reference_mark_manager` |
| FR-20 | A new mark takes the first configured shape that no mark uses yet. If all are in use, it takes the first configured shape. Its angle and color come from the options. | `models/slicing/slice.py::_select_unique_shape` | `test_slice_process_reference_marks` |
| FR-21 | A new mark's size is `--mark-size` when it is set. Otherwise it is `int(distance from the model origin / 10)`, limited to 3 through 5. | `models/slicing/slice.py::_calculate_mark_size` | `test_slice_mark_size` |
| FR-22 | After marks are chosen, any mark closer than `min_distance` to a contour boundary, or to a mark already kept, is dropped. The earlier mark stays. If a slice then has a contour with no mark, one warning is logged for the slice (`No reference mark fits N of M contours in slice I. Try a smaller --mark-min-distance.`). The slice is still written. | `models/reference_marks/reference_mark_adjuster.py` | `test_reference_mark_adjuster`, `test_reference_mark_adjuster_extra`, `test_slice_process_reference_marks`, `test_end_to_end` |
| FR-23 | The mark settings are checked when created: `available_shapes` must not be empty, `tolerance` and `min_distance` must not be negative, `size`, when set, must be greater than 0, and `size`, `tolerance`, `min_distance` and `angle` must be finite. Violations raise `ValueError`. | `models/reference_marks/config.py` | `test_reference_mark_config` |

### SVG output

| ID | Requirement | Code | Tests |
|---|---|---|---|
| FR-24 | One SVG file is written per slice, named `slice_000.svg`, `slice_001.svg` and so on, including empty slices (a slice whose cut misses the mesh). | `writers/svg_writer.py`, `utils/file_operations.py` | `test_file_operations`, `test_svg_output`, `test_end_to_end` |
| FR-25 | Each SVG has, in order: the polygon outlines (black, no fill; a polygon with holes has one outline for the outer edge and one for each hole), the marks, and the text `Slice N` once per polygon. The label sits at the polygon centroid. If that is outside the polygon, it sits at the centre of the bounding box. If that is outside too, it sits at a point that is inside the polygon. | `svg/slice_svg_drawer.py` | `test_svg_output` |
| FR-26 | Points are drawn at `(x, −y)` in model units, so the picture has the same handedness as the model seen from above (SVG's y axis points down). Marks are flipped the same way, including their angle. Every SVG has the same `viewBox`. It holds the outlines of all slices plus a margin of 5% of the larger side, so layers can be laid over each other. The root sets `width` and `height` to the viewBox width and height followed by the unit of `--units` (FR-31), for example `33.0cm`, so every file has the same physical size and a laser program can read it. The root also sets `font-size` to 1/20 and `stroke-width` to 1/200 of the viewBox's larger side. When no slice has an outline, there is no `viewBox`, and `width` and `height` are 100%. | `svg/svg_generator.py`, `svg/slice_svg_drawer.py` | `test_svg_output`, `test_end_to_end` |
| FR-27 | Mark shapes, all unfilled. Circle: diameter is the size, default red. Square: side is the size, default blue. Triangle: 2 × size wide and tall, default green. Arrow: a line as long as the size with a head, default black. The color option replaces the default. Angle turns the shape. Angles are in radians everywhere inside the package; only the `--mark-angle` option takes degrees. | `svg/drawing/strategies/*`, `domain/shapes/*` | `test_svg_output`, `test_arrow_drawing_strategy` |
| FR-28 | `ShapeFactory.get_shape` raises `ValueError: Unknown shape type` for an unknown shape name. The command checks `--available-shapes` against the registered shapes first, and an unknown or empty list stops it with `Invalid value for --available-shapes` and exit code 2. | `svg/drawing/shape_factory.py`, `cli.py::resolve_settings` | `test_shape_factory`, `test_process_model_validation`, `test_cli_checks_before_prompt` |
| FR-29 | Code can add shapes (`register_shape`) and mesh loaders (`LoaderFactory.register_loader`). The CLI uses only the four built-in shapes and the trimesh loader. | `svg/drawing/shape_factory.py`, `models/loading/__init__.py` | `test_shape_factory`, `test_loader_factory` |

## Non-functional requirements

| ID | Requirement | Where it is enforced |
|---|---|---|
| NFR-1 | Python 3.12 or newer. CI runs 3.12, 3.13 and 3.14 on Linux. | `pyproject.toml` (`requires-python`), `.github/workflows/tests.yaml` |
| NFR-2 | Runtime dependencies are declared in `pyproject.toml` and locked in `uv.lock`: click, pydantic, scipy, networkx, shapely, svgwrite, trimesh. Installing the package pulls in all of them. | `pyproject.toml`, `uv.lock` |
| NFR-3 | Every pull request passes `ruff check`, `ruff format --check`, `pyright` (strict on `src/`) and the full test suite. | `.github/workflows/tests.yaml` |
| NFR-4 | The command installs as `layerforge` with `uv tool install`, and the wheel contains every module. | `pyproject.toml` (`[project.scripts]`) |
| NFR-5 | Bad option values fail before any work starts, with a message that names the option. Click reports usage errors with exit code 2. A bad config file also exits with 2, with a message that names the file and the key (FR-30). A conflict between options exits with 1. The command asks for `--stl-file` only after these checks pass. A missing, unreadable or empty mesh file, or a mesh with no height, stops the command with a message that names the file and exit code 1. | `cli.py`, `models/model_factory.py` |
| NFR-6 | Documentation builds with `mkdocs build --strict` and deploys to GitHub Pages on each push to `main`. | `.github/workflows/docs.yaml` |
| NFR-7 | The code is licensed CC BY-NC 4.0. A commercial license is offered separately. | `LICENSE`, `COMMERCIAL_LICENSE` |
| NFR-8 | The tool logs only through the standard `logging` module and sets no log configuration. Warnings therefore reach stderr through Python's last-resort handler. | `models/slicing/slice.py` |

The earlier goals to bundle all dependencies into one binary and to run without a Python install are withdrawn. They depended on PyOxidizer, which was removed because its build file was an unedited template that could not build the tool.

## Constraints

- **C-1.** Slicing is along the z axis only, with z pointing up.
- **C-2.** One mesh per file. The mesh has no unit. `--units` (default `mm`) states it and labels the size of each SVG (FR-31). Nothing converts a number.
- **C-3.** Mesh formats are whatever trimesh can read. Only STL is tested.
- **C-4.** All work happens in one process, in memory. Mesh size is limited by memory.

## Known gaps

These are places where current behavior differs from the intent in the project docs, or where behavior is likely to surprise. Each was checked against the current code.

| ID | Gap | Evidence | Effect |
|---|---|---|---|
| G-4 (#60) | Only one mark per polygon (FR-15), and nothing checks that adjacent layers can be aligned in exactly one way. | `get_stable_marks`. The first mark is usually a circle, which has no direction. | One mark fixes position but not rotation. A cube or cylinder can be stacked rotated. Target: TR-1 to TR-4, TR-12. |
| G-5 (#61) | Shapes are chosen by list order, not by need (FR-20). Once all are used, every new mark is the first shape. | `_select_unique_shape` | The first mark is a circle and cannot fix rotation. The algorithm page says shapes cycle. Target: TR-8. |
| G-6 (#62) | Mark size comes from the distance to the model origin, clamped to 3 to 5 units (FR-21). | `_calculate_mark_size` | It does not follow the sheet thickness. The development notes say it should follow the model's scale, and the target says the sheet thickness instead. Target: TR-6. |
| G-7 (#63) | Marks are shared by all slices, not chosen for pairs of adjacent layers (FR-19). | One `ReferenceMarkManager` per run. | A mark can be inherited from a slice far away, and nothing makes the shared marks lie in both outlines. Target: TR-9. |
| G-16 (#73) | Overlapping shells in one mesh give false holes (FR-13). Decided 2026-09-25: a documented limit, not fixed. | Two 20 mm boxes, 10 mm apart in x, cut to one polygon of area 566.7 with a hole. The real region is one solid of area 600. | The even-odd rule treats an overlap as a hole. Users merge bodies before export (see Getting Started). trimesh drops loop winding after `section().to_2D()`, so a union of the loops cannot tell a cavity from an overlap. A later opt-in union of the mesh with `manifold3d` before slicing would work for watertight bodies. |
| G-18 (#75) | The label can cross an outline (FR-25). | The centroid of a concave polygon can lie near an edge. | The text runs over the outline. The first mark and the number can also sit on the same point. Target: TR-11. |
| G-19 (#76) | The default `min_distance` ignores the model size (FR-17). | A 10 mm cube gets no marks with the default 10. | Only the warning from FR-22 tells the user. Target: TR-6. |
| G-20 (#84) | Shapes have no common definition (FR-27). The arrow is a line and an open head, anchored at its tail. Square and circle sizes are a side and a diameter. The triangle's size is half its width. Angle 0 points along +x for the arrow and up for the triangle. | `svg/drawing/strategies/*`, `domain/shapes/*` | An arrow cannot be cut as a hole, and marks of one size are not comparable. Target: TR-7. |
| G-21 (#85) | Clearance and spacing use the mark's centre, not its whole hole (FR-17, FR-22). | `get_stable_marks`, `ReferenceMarkAdjuster` | A large mark can touch the outline or another mark. Target: TR-5. |
| G-23 (#83) | The output suits a screen, not a laser (FR-25, FR-27). Outlines are black, holes use a colour per shape, the root sets a stroke width of 1/200 of the drawing, and the label is 1/20 of it. | `svg/svg_generator.py`, `svg/drawing/strategies/*` | Laser software may read the strokes as areas to engrave, treat colours as different operations, and get text too small to engrave. Target: TR-11, TR-14. |
| G-30 (#145) | A bad `--mark-color` ends in a traceback while the SVG is drawn (NFR-5). | svgwrite rejects the value when the first mark is drawn. | `TypeError: 'notacolor' is not a valid value for attribute 'stroke'`, exit 1, after the slicing. #83 removes the option and needs the same check for its colour options. |

Fixing these is not part of this page. Each has its own issue, given in brackets.
