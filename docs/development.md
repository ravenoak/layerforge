# Development

## Requirements

The functional and non-functional requirements, constraints and known gaps are
on the [Requirements](requirements.md) page. The same behavior is written as a
formal Allium specification in `specs/layerforge.allium`. Check it with:

```bash
allium check specs/layerforge.allium
```

## Pseudocode

This is the intended design. Where the code differs, see the known gaps on the
[Requirements](requirements.md#known-gaps) page.

1. Load the 3D Model:
    1. Read an STL file to load the model into the application.
2. Scale the Model:
    1. If a scale factor is provided, scale the model by this factor.
    2. If a target height is provided, calculate the necessary scale factor to achieve this height and apply it to the model, ensuring the aspect ratios are maintained.
3. Calculate the Model Origin:
    1. Determine the model's origin point for reference in subsequent operations.
4. Slice the Model into Layers:
    1. Determine the positions for each slice based on the specified layer height.
    2. For each determined position:
        1. Slice the model at this position.
        2. Project the resulting slice to a 2D plane.
        3. Create a List of `Polygon`s representing the 2D contours of the slice.
5. For each slice, process the slice:
    1. Calculate Reference Marks:
        1. Evaluate candidate points using a geometric stability metric derived from GDOP.
        2. Use the ReferenceMarkManager to inherit marks from adjacent slices when possible or create new marks that maximise stability, ensuring:
           * Marks are inherited from adjacent slices where possible.
           * New marks are assigned a unique shape if not inherited.
           * Marks do not overlap and are contained within the model's contours.
           * Marks are not placed on the model's edges.
           * The distance between marks is appropriate for the model's scale.
           * The size of the marks is proportional to the model's scale, ensuring visibility.
    2. Adjust Reference Marks:
        1. Adjust the positions of the reference marks to avoid overlaps, using the ReferenceMarkAdjuster.
    3. Generate SVG File:
        1. Draw the slice contours.
        2. Add the adjusted reference marks.
        3. Annotate the slice with its number within the contour area.
6. Output:
    1. Save the generated SVG files to the specified output directory, with each file representing a slice of the original 3D model.

## Expected Workflow

1. Build a :class:`Model` using :class:`ModelFactory` and the desired mesh loader.
2. Call :meth:`SlicerService.slice_model` to produce a list of :class:`Slice` objects.
3. Use :class:`ReferenceMarkService` to process each slice so reference marks are calculated and adjusted.
4. Pass the processed slices to :class:`SVGGenerator` (via the CLI or directly) to write SVG files.

## Running the Tests

```bash
uv sync
uv run pytest
```

`uv sync` installs the runtime dependencies and the `dev` group (pytest and
hypothesis). Add `--group docs` to build the documentation with
`uv run mkdocs build --strict`.

## Linting and Type Checking

```bash
uv run ruff check
uv run ruff format --check
uv run pyright
```

pyright runs in `strict` mode on `src/` and `standard` mode on `tests/` and `scripts/`.
CI runs all three on every pull request.

## Working Notes

- Run the checks so that a failure is not hidden. Do not pipe them through
  `tail` in an `&&` chain, because the pipe returns the exit code of `tail`.
  Run `uv run ruff format` before `ruff check` and `pyright`.
- `Trimesh.section` takes `(plane_normal, plane_origin)` when called with
  positional arguments. Pass both by keyword.
- `Path3D.to_2D()` without a transform re-centres every cut. Slices must use the
  transform in `Model.calculate_slice_contours` to share one frame.
- `trimesh.creation.extrude_polygon` needs a triangulation engine that is not
  installed. Tests build shapes with `extrude_triangulation` or the primitives
  in `trimesh.creation` instead.
- To look at an SVG, render it with `rsvg-convert -w 500 -b white in.svg -o out.png`.
  Do not use `qlmanage`, which can hang.
- Slice positions are the middle of each layer. A cut exactly on a face of the
  mesh comes out empty.

## Common Error Messages

- `ModuleNotFoundError: No module named 'networkx'` or `'scipy'` – `trimesh`
  needs both for slicing. Both are declared dependencies, so this means the
  environment was not created with `uv sync`.
