# Development

## Project Requirements

### Functional Requirements

1. **Load 3D Model**:
    - Read an STL file and load the model.

2. **Scaling**:
    - Scale the model using either a multiplier or a target height while maintaining aspect ratios.

3. **Slicing**:
    - Slice the model into layers of a specified thickness.

4. **Reference Marks**:
    - Reference marks should be placed at the centroid of each slice, where appropriate.
    - Reference marks should be inherited from adjacent slices where possible, including the shape of the mark.
    - New reference marks should be a different shape when added to a slice where they are not inherited.
    - New reference marks must be introduced to a layer that does have a reference mark inherited from an adjacent slice, to ensure there is continuity in the reassembly process.
    - Ensure marks are aligned with adjacent slices.
    - Marks must not overlap and must be inside the model's contours.
    - Marks must not be placed on the contour's edges.
    - Marks must not exceed the contour's boundaries.
    - The distance between marks should be within the scale of the overall model.
    - The size of the marks should be proportional to the model's scale, while maintaining visibility.
    - The marks need to be able to be used to properly align the slices during reassembly, including rotational alignment in addition to translational alignment.

5. **SVG Generation**:
    - Generate an SVG file for each slice.
    - Include contours, reference marks, and slice numbers.
    - Each slice should be labeled with its number within the contour area.

### Non-Functional Requirements

- The application should bundle all dependencies to mimic a statically compiled binary.
- The executable should run on different platforms without requiring a Python installation.

## Pseudocode

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

The test suite depends on optional libraries such as `shapely` and `trimesh`. Each
test module calls `pytest.importorskip` for these imports so that tests are
skipped if the dependencies are unavailable. Install these packages to execute
the entire suite.

## Building a Standalone Executable

LayerForge uses [PyOxidizer](https://github.com/indygreg/PyOxidizer) to bundle the application and its dependencies into a single binary. As mentioned in the [README](../README.md#features), "Pyoxidizer packaging enables simple cross-platform distribution."

### Requirements

- Rust toolchain (\`cargo\` and \`rustc\`)
- Python 3.12 or newer
- PyOxidizer installed via `pip install pyoxidizer`
- Supported on Linux and Windows

### Build Steps

Run the following from the project root:

```bash
pyoxidizer build
```

The resulting executable will be placed under `build/`.

### Troubleshooting

- **Missing Rust toolchain**: install Rust from [rustup.rs](https://rustup.rs) and ensure `cargo` is on your `PATH`.
- **Incorrect Python version**: PyOxidizer must use Python 3.12+. Set `PYTHON_SYS_EXECUTABLE` if multiple versions are installed.
- **Windows build errors**: run from a Developer Command Prompt so that MSVC tools are available.
- **Anti-virus interference**: some security tools may quarantine the generated binary. Whitelist the output directory if needed.
