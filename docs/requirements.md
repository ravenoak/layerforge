# Requirements

This page lists what LayerForge does today, derived from the code and tests as of 2026-09. It describes current behavior, not intended behavior. Where the two differ, the difference is listed under [Known gaps](#known-gaps).

The same behavior is written as a formal specification in [`specs/layerforge.allium`](https://github.com/ravenoak/layerforge/blob/main/specs/layerforge.allium). The rule names there match the IDs here.

## Purpose

LayerForge slices a 3D mesh into horizontal layers. It writes one SVG file per layer. Each SVG has the layer outline, numbered reference marks, and a slice number. A person cuts the layers, stacks them, and uses the marks to align them.

## How to read this page

- **FR** is a functional requirement. **NFR** is a non-functional requirement. **C** is a constraint.
- **Code** names the module and symbol (`path::symbol`). Line numbers are left out because they drift.
- **Tests** names the test files that cover the requirement. A dash means no test covers it directly.
- Paths are relative to `src/layerforge/` for code and `tests/` for tests.

## Functional requirements

### Command line

| ID | Requirement | Code | Tests |
|---|---|---|---|
| FR-1 | The `layerforge` command takes `--stl-file`. If it is missing, the command prompts for it. | `cli.py::cli` | `test_cli` |
| FR-2 | `--layer-height` is a number greater than 0. The default is 3.0. A value of 0 or less stops the command with `Invalid value for --layer-height: must be > 0` and exit code 2. | `cli.py::process_model` | `test_process_model_validation`, `test_cli` |
| FR-3 | `--scale-factor` and `--target-height`, when given, must be greater than 0. Both fail the same way as FR-2. | `cli.py::process_model` | `test_process_model_validation` |
| FR-4 | `--scale-factor` and `--target-height` cannot be used together. The command prints `Only one of scale_factor or target_height can be provided.` and exits with code 1. | `cli.py::process_model`, `cli.py::cli` | `test_cli` |
| FR-5 | `--output-folder` sets where SVG files go. The default is `output`. The folder and its parents are created if missing. | `utils/file_operations.py`, `writers/svg_writer.py` | `test_file_operations`, `test_end_to_end` |
| FR-6 | Mark options: `--mark-tolerance` (default 10.0), `--mark-min-distance` (default 10.0), `--available-shapes` (comma-separated, default `circle,square,triangle,arrow`), `--mark-angle` (degrees, default 0.0), `--mark-color` (default none). Shape names are trimmed and empty items dropped. The angle is converted to radians. | `cli.py::process_model` | `test_cli` |

### Loading and scaling

| ID | Requirement | Code | Tests |
|---|---|---|---|
| FR-7 | The mesh is read with trimesh. A file that holds more than one geometry is rejected with a `ValueError`. | `models/loading/implementations/trimesh_loader.py`, `models/model_factory.py` | `test_trimesh_loader`, `test_model_factory` |
| FR-8 | With `--scale-factor`, the mesh is scaled uniformly by that factor about the coordinate origin. | `models/model_factory.py::_scale_mesh` | `test_model_factory`, `test_end_to_end` |
| FR-9 | With `--target-height`, the mesh is scaled uniformly so its height (maximum z minus minimum z) equals the target. | `models/model_factory.py::_scale_mesh` | `test_model_factory`, `test_end_to_end` |
| FR-10 | The model origin is the centre of the mesh bounding box in x and y, taken after scaling. The mesh is not moved. | `models/model_factory.py::_calculate_origin` | `test_model_factory` |

### Slicing

| ID | Requirement | Code | Tests |
|---|---|---|---|
| FR-11 | The model height is maximum z minus minimum z. | `models/model.py::calculate_height` | - |
| FR-12 | Slice positions are `i × layer_height` for `i` from 0 up to `ceil(height / layer_height) − 1`, at least one. The last position is always equal to the model height, added if the steps stop short of it. For height 10 and layer height 3 the positions are 0, 3, 6, 9, 10. | `models/slicing/slicer_service.py::calculate_slice_positions` | `test_slicer_service` |
| FR-13 | Each position is a horizontal plane (normal +z). The cut through the mesh gives closed loops. Each loop becomes one polygon in a flat 2D frame. A plane that cuts nothing gives an empty list of polygons. | `models/model.py::calculate_slice_contours` | `test_end_to_end` |
| FR-14 | One slice is made per position, in order and numbered from 0. Empty slices are kept. | `models/slicing/slicer_service.py::slice_model` | `test_end_to_end` |

### Reference marks

| ID | Requirement | Code | Tests |
|---|---|---|---|
| FR-15 | Each polygon gets at most one mark. | `models/reference_marks/reference_mark_calculator.py::get_stable_marks` | `test_reference_mark_calculator`, `test_reference_mark_property` |
| FR-16 | Candidate points for a polygon are its centroid plus random points inside its bounding box that fall inside the polygon (up to 40 tries, 4 wanted). The random generator has a fixed seed, so the same polygon always gives the same points. | `models/reference_marks/reference_mark_calculator.py::_sample_points` | `test_calculator_get_potential_marks` |
| FR-17 | A point qualifies only if it is at least `min_distance` from the polygon boundary and from marks already chosen in the same slice. | same | `test_reference_mark_property` |
| FR-18 | An earlier mark that qualifies and lies inside the polygon is reused. Otherwise the qualifying candidate with the highest stability score wins. The score is the sum of distances between all pairs of points, the candidate and the marks already chosen. | same | `test_calculator_get_potential_marks`, `test_reference_mark_property` |
| FR-19 | Marks are shared across all slices in one run. A chosen point that lies within `tolerance` of an earlier mark inherits its shape, size, angle and color. | `models/slicing/slice.py::process_reference_marks`, `models/reference_marks/reference_mark_manager.py` | `test_slice_mark_inheritance`, `test_slice_process_reference_marks`, `test_reference_mark_manager` |
| FR-20 | A new mark takes the first configured shape that no mark uses yet. If all are in use, it takes the first configured shape. Its angle and color come from the options. | `models/slicing/slice.py::_select_unique_shape` | `test_slice_process_reference_marks` |
| FR-21 | A new mark's size is `int(distance from the model origin / 10)`, limited to 3 through 5. | `models/slicing/slice.py::_calculate_mark_size` | `test_slice_mark_size` |
| FR-22 | After marks are chosen, any mark closer than `min_distance` to a contour boundary, or to a mark already kept, is dropped. The earlier mark stays. | `models/reference_marks/reference_mark_adjuster.py` | `test_reference_mark_adjuster`, `test_reference_mark_adjuster_extra` |
| FR-23 | The mark settings are checked when created: `available_shapes` must not be empty, and `tolerance` and `min_distance` must not be negative. Violations raise `ValueError`. | `models/reference_marks/config.py` | `test_reference_mark_config` |

### SVG output

| ID | Requirement | Code | Tests |
|---|---|---|---|
| FR-24 | One SVG file is written per slice, named `slice_000.svg`, `slice_001.svg` and so on, including empty slices. | `writers/svg_writer.py`, `utils/file_operations.py` | `test_file_operations`, `test_svg_output`, `test_end_to_end` |
| FR-25 | Each SVG has, in order: the polygon outlines (black, no fill), the marks, and the text `Slice N` once per polygon. The label sits at the polygon centroid, or at the centre of its bounding box if the centroid is outside the polygon. | `svg/slice_svg_drawer.py` | `test_svg_output` |
| FR-26 | The SVG has no size or viewBox. Its coordinates are the 2D coordinates of FR-13, in model units. | `svg/svg_generator.py` | - |
| FR-27 | Mark shapes, all unfilled. Circle: diameter is the size, default red. Square: side is the size, default blue. Triangle: 2 × size wide and tall, default green. Arrow: a line as long as the size with a head, default black. The color option replaces the default. Angle turns the shape. | `svg/drawing/strategies/*`, `domain/shapes/*` | `test_svg_output`, `test_arrow_drawing_strategy` |
| FR-28 | An unknown shape name raises `ValueError: Unknown shape type`. This happens when the shape is drawn, not when options are read. | `svg/drawing/shape_factory.py` | `test_shape_factory` |
| FR-29 | Code can add shapes (`register_shape`) and mesh loaders (`LoaderFactory.register_loader`). The CLI uses only the four built-in shapes and the trimesh loader. | `svg/drawing/shape_factory.py`, `models/loading/__init__.py` | `test_shape_factory`, `test_loader_factory` |

## Non-functional requirements

| ID | Requirement | Where it is enforced |
|---|---|---|
| NFR-1 | Python 3.12 or newer. CI runs 3.12, 3.13 and 3.14 on Linux. | `pyproject.toml` (`requires-python`), `.github/workflows/tests.yaml` |
| NFR-2 | Runtime dependencies are declared in `pyproject.toml` and locked in `uv.lock`: click, pydantic, scipy, networkx, shapely, svgwrite, trimesh. Installing the package pulls in all of them. | `pyproject.toml`, `uv.lock` |
| NFR-3 | Every pull request passes `ruff check`, `ruff format --check`, `pyright` (strict on `src/`) and the full test suite. | `.github/workflows/tests.yaml` |
| NFR-4 | The command installs as `layerforge` with `uv tool install`, and the wheel contains every module. | `pyproject.toml` (`[project.scripts]`) |
| NFR-5 | Bad option values fail before any work starts, with a message that names the option. Click reports usage errors with exit code 2. A conflict between options exits with 1. Other failures (missing file, unreadable mesh) end with a Python traceback and exit code 1. | `cli.py` |
| NFR-6 | Documentation builds with `mkdocs build --strict` and deploys to GitHub Pages on each push to `main`. | `.github/workflows/docs.yaml` |
| NFR-7 | The code is licensed CC BY-NC 4.0. A commercial license is offered separately. | `LICENSE`, `COMMERCIAL_LICENSE` |
| NFR-8 | The tool logs only through the standard `logging` module and sets no log configuration. | `models/slicing/slice.py` |

The earlier goals to bundle all dependencies into one binary and to run without a Python install are withdrawn. They depended on PyOxidizer, which was removed because its build file was an unedited template that could not build the tool.

## Constraints

- **C-1.** Slicing is along the z axis only, with z pointing up.
- **C-2.** One mesh per file. Units are whatever units the mesh uses. Nothing converts them.
- **C-3.** Mesh formats are whatever trimesh can read. Only STL is tested.
- **C-4.** All work happens in one process, in memory. Mesh size is limited by memory.

## Known gaps

These are places where current behavior differs from the intent in the project docs, or where behavior is likely to surprise. Each was checked against the current code. G-2 and G-3 were also reproduced by running trimesh 5.1 directly; the numbers are in the Evidence column.

| ID | Gap | Evidence | Effect |
|---|---|---|---|
| G-1 | Slice positions start at z = 0, not at the lowest point of the mesh (FR-12). | `slicer_service.py::calculate_slice_positions` uses `i × layer_height` only. | A mesh centred on z = 0 loses its lower half and gets empty slices at the top. The end-to-end test uses a box that sits on z = 0. |
| G-2 | The 2D frame differs for each slice (FR-13). trimesh centres each cut on its own vertices. | A 20 mm box moved to x = 100, y = 50 gives 2D bounds of ±10 at every height. A 30° tilted box has its slice centre move from x = −6.87 at z = 5 to x = 6.0 at z = 30, while the 2D coordinates stay near 0. | Marks and SVG coordinates are not in model coordinates. A mark inherited by position (FR-19) compares points from different frames. |
| G-3 | Holes are drawn as solid shapes (FR-13). | A tube (annulus, radii 5 and 10) gives two closed polygons, areas 312.1 and 78.0. | A mark can land inside a hole. Handling holes needs trimesh's `polygons_full`, which also needs the `rtree` package. |
| G-4 | Only one mark per polygon (FR-15). | `get_stable_marks` | One mark fixes position but not rotation. The requirement in the development notes for rotational alignment is not met. |
| G-5 | Shapes do not cycle (FR-20). Once all are used, every new mark is the first shape. | `_select_unique_shape` | Marks are harder to tell apart on large models. The algorithm page says shapes cycle. |
| G-6 | Mark size is fixed at 3 to 5 units (FR-21). | `_calculate_mark_size` | It does not scale with the model, and the development notes say it should. |
| G-7 | Marks are shared by all slices, not only neighbours (FR-19). | One `ReferenceMarkManager` per run. | A mark can be inherited from a slice far away. |
| G-8 | Angle units are mixed. Options and config use radians after conversion. The arrow treats values above 2π as degrees. `docs/configuration.md` says degrees. | `arrow_strategy.py`, `test_arrow_drawing_strategy` | An angle of 90 in config is read as degrees by the arrow and as radians by circles and triangles. |
| G-10 | The last slice lies on the top face and comes out empty for a box (FR-12, G-1). | `test_end_to_end` skips it. | One useless SVG per run for flat-topped models. |
| G-11 | Some bad inputs are not caught up front (NFR-5). A mesh with zero height and `--target-height` raises `ZeroDivisionError`. An unknown shape name fails only when drawn. | `model_factory.py`, `shape_factory.py` | Users see a traceback. |
| G-12 | The SVG has no viewBox and does not flip the y axis (FR-26). | Sample output has negative coordinates and `width="100%"`. | Viewers may crop the drawing or show it mirrored. |
| G-13 | Marks that fit no polygon are dropped silently (FR-17, FR-22). | `test_end_to_end` scaled cases need `--mark-min-distance 2`. | A small model with default options gets slices with no marks and no warning. |

Fixing these is not part of this page. Each is a candidate for its own issue.
