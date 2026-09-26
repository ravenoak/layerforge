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
illustrative session using a 20 mm cube. Each 5 mm layer is cut at its middle, so the cube gives four layers and the command writes four files:

```text
$ layerforge --stl-file cube.stl --layer-height 5 --output-folder demo_output
exit 0

files [demo_output/slice_000.svg, ..., demo_output/slice_003.svg]
```

Opening the first SVG shows the contour, one reference mark (the red circle) and the slice label:

```xml
<?xml version="1.0" encoding="utf-8" ?>
<svg ...>
  <polygon fill="none" ... />
  <circle ... stroke="red" />
  <text ...>Slice 0</text>
</svg>
```

## Common Errors

Each message below was copied from a run of the command. The command checks the
options and the settings file before it asks for the STL path. A message that
starts with `Error:` and exits with code 2 is also preceded by a `Usage:` line.

- ``Error: Invalid value for --layer-height: must be > 0`` (exit code 2) – a
  number option is 0 or less. The message names the option. `nan` and `inf` give
  `must be a finite number`. `--kerf`, `--mark-tolerance` and `--mark-min-distance` may be 0,
  and give `must be >= 0` below that.
- ``Error: bad.toml: marks.tolerance: must be >= 0`` (exit code 2) – the
  [config file](configuration.md#config-file) has a bad value. The message is
  `<file>: <key>: <reason>`. An unknown key gives
  ``Error: typo.toml: layer_hieght: Extra inputs are not permitted``.
- ``Error: Invalid value for '--units': 'ft' is not one of 'mm', 'cm', 'in'.``
  (exit code 2) – `--units` takes `mm`, `cm` or `in`.
- ``Error: Invalid value for --output-folder: ofile is not a folder`` (exit code 2)
  – the output folder is a file, or would have to be made inside one.
- ``Only one of scale_factor or target_height can be provided.`` (exit code 1, on
  standard output) – give `--scale-factor` or `--target-height`, not both.
- ``Error: Cannot load 'nope.stl': string is not a file: `nope.stl` `` (exit code 1)
  – check the `--stl-file` path. A file that is not a mesh gives
  ``Error: Cannot load 'junk.stl': the mesh contains no geometry``.
- ``WARNING:root:No reference mark fits 1 of 1 contours in slice 0. Try a smaller --mark-min-distance or --mark-size.``
  (the run continues, exit code 0; the numbers vary) – the mark and the material around it
  do not fit the piece. By default a mark is as big as the layer height, and a hole needs half the
  layer height of material around it. A square piece 6 mm wide or less gets no mark at a layer
  height of 3, and a 10 mm cube gets none at a layer height of 5. Use a smaller `--mark-size` or
  `--mark-min-distance`.
- ``WARNING:root:The mark size 1 is below the least hole size 3 for a sheet of 3 and a kerf of 0.3 (TR-6). Holes this small may not cut cleanly.``
  (the run continues, exit code 0) – `--mark-size` is smaller than the larger of the layer height
  and 1.5 times the kerf. Your laser may not cut a hole that small. Raise `--mark-size`, or ignore
  the warning if you know your machine.
- A slice shows a hole where two parts of the model overlap – the STL holds
  overlapping closed shells, for example two boxes saved as one file without a
  union. LayerForge cuts loops by the even-odd rule, so the overlap becomes a
  hole. Merge the bodies with a boolean union in your CAD or mesh tool before
  export. See G-16 in the [known gaps](requirements.md#known-gaps).
