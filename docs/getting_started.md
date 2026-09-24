# Getting Started

## Installation

Install [uv](https://docs.astral.sh/uv/getting-started/installation/), then install the command-line tool:

```bash
uv tool install git+https://github.com/ravenoak/layerforge
```

To work on the code, clone the repository and run `uv sync`. All runtime
dependencies, including `scipy` and `networkx`, are installed by default.

## Usage

1. Place the STL file in the project directory.
2. Set the desired layer height and scale parameters.
3. Run the application.
4. Find the generated SVG files in the specified output directory.

5. Verify the installed version:
   ```bash
   python -c "import layerforge; print(layerforge.__version__)"
   ```

## Example

To try LayerForge without providing your own STL file, run the sample script:

```bash
python scripts/simple_mesh_example.py
```

This generates a basic cube mesh, slices it, and writes SVG files to the
`example_output/` directory.

## CLI Example

Running the CLI directly mirrors the example script.  Below is an
illustrative session using a temporary cube mesh:

```text
$ python -m layerforge.cli --stl-file cube.stl --layer-height 5 --output-folder demo_output
exit 0

files [demo_output/slice_000.svg, demo_output/slice_001.svg, demo_output/slice_002.svg]
```

Opening the first SVG shows the slice label and contour:

```xml
<?xml version="1.0" encoding="utf-8" ?>
<svg ...>
  <polygon fill="none" ... />
  <text ...>Slice 0</text>
</svg>
```

## Common Errors

- `ModuleNotFoundError: No module named 'trimesh'` – install the optional
  dependencies listed above.
- `FileNotFoundError: [Errno 2] No such file or directory` – check the
  provided `--stl-file` path.
- `ConflictingOptionsError: Only one of scale_factor or target_height can be provided.`
