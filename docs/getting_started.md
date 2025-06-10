# Getting Started

## Installation

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
