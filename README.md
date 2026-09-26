# LayerForge

[![Build Documentation using MkDocs](https://github.com/ravenoak/layerforge/actions/workflows/docs.yaml/badge.svg)](https://github.com/ravenoak/layerforge/actions/workflows/docs.yaml)
[![Run Tests](https://github.com/ravenoak/layerforge/actions/workflows/tests.yaml/badge.svg)](https://github.com/ravenoak/layerforge/actions/workflows/tests.yaml)

## Description

A 3D Model Slicing and SVG Generation Application

## Table of Contents

- [Installation](#installation)
- [Dependencies](#dependencies)
- [Usage](#usage)
- [Features](#features)
- [Configuration](#configuration)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

<!-- - [Acknowledgements](#acknowledgements) -->

## Installation

1. Install [uv](https://docs.astral.sh/uv/getting-started/installation/). uv fetches a matching Python (3.12 or newer) if needed.
2. Install the command-line tool:
   ```bash
   uv tool install git+https://github.com/ravenoak/layerforge
   ```
3. To work on the code, clone the repository and create the environment:
   ```bash
   uv sync
   uv run pytest
   ```

## Dependencies

The following Python packages are required at runtime:

- `trimesh` – mesh loading and manipulation
- `svgwrite` – generating SVG files
- `shapely` – geometric computations
- `pydantic` – configuration validation
- `scipy`, `networkx` – needed by `trimesh` for slicing

These packages are installed automatically when installing LayerForge.

## Usage

Run the CLI to slice an STL model and produce SVGs:

```bash
layerforge --stl-file model.stl --layer-height 3.0 --output-folder output
```

Optional flags let you scale the model and control marker placement. Use `layerforge --help` for all options.

## Checking the Version

Use Python to display the installed package version:
```bash
python -c "import layerforge; print(layerforge.__version__)"
```

## Features

- Slice STL models into individual layers.
- Generate SVG files with contours, slice numbers and reference marks.
- Reference marks are chosen using a geometric stability metric inspired by GDOP.
- Marks inherit shape, position and angle between slices and are adjusted to avoid overlaps.
- Supports multiple mark shapes (circle, square, triangle, arrow) for easy identification.

## Configuration

The CLI exposes parameters for tuning reference mark generation:

- `--config` – a TOML settings file. Without it, `layerforge.toml` in the current directory is read if it exists, and the command says so on stderr. The command line beats the file. See [docs/configuration.md](docs/configuration.md#config-file).
- `--units` – the unit of the model and of every length option: `mm`, `cm` or `in`. It sets the physical size of each SVG, so a laser program imports it at the right scale. An STL file has no unit, so this states it. A length that you give is not converted; the defaults for the layer height (3 mm) and the kerf (0.3 mm) are stated in this unit.
- `--kerf` – the width of material the tool removes. It sets the smallest default mark size. Default 0.3 mm, stated in `--units`. Use 0 for a CNC router or hand work.
- `--mark-size` – size of every new mark. Without it the size is the larger of the layer height (the sheet thickness) and 1.5 times the kerf, so it does not depend on the size of the model.
- `--mark-tolerance` – distance used when matching an existing mark. Without it, 0.1 times the mark size.
- `--mark-min-distance` – minimum distance from contours and between marks. Without it, the mark size.
- `--available-shapes` – comma separated list of shapes to choose from when creating marks.
- `--mark-angle` – default orientation angle for generated marks in degrees.
- `--cut-color` and `--engrave-color` – the colours of the cut lines (default red) and of the number (default black).

The default of each option is in the [keys table](docs/configuration.md#config-file) and in `--help`.

See [docs/reference_mark_algorithm.md#parameter-effects](docs/reference_mark_algorithm.md#parameter-effects)
for diagrams and tuning tips on how these options influence mark placement.

## Contributing

Contributions are welcome! Please read our [Code of Conduct](CODE_OF_CONDUCT.md)
before participating in this project.

Changes that a user can see are listed in [CHANGELOG.md](CHANGELOG.md), which also
states the version policy. A pull request that changes options, defaults, exit
codes, output files or public functions adds a line under `Unreleased`.

## License

This project is licensed under the Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0) License
for non-commercial use. For commercial use, please contact Caitlyn O'Hanna at caitlyn.ohanna@gmail.com to
obtain a commercial license.

For more details, see the [LICENSE](LICENSE) file for non-commercial use and
the [COMMERCIAL_LICENSE](COMMERCIAL_LICENSE) file for commercial use.

## Contact

For questions, comments, or concerns, please contact Caitlyn O'Hanna at caitlyn.ohanna@gmail.com.
Citation information is available in [CITATION.cff](CITATION.cff).

<p><a property="dct:title" rel="cc:attributionURL" href="https://github.com/ravenoak/layerforge">LayerForge</a> by <a rel="cc:attributionURL dct:creator" property="cc:attributionName" href="https://github.com/ravenoak">Caitlyn O'Hanna</a> is licensed under <a href="https://creativecommons.org/licenses/by-nc/4.0/?ref=chooser-v1" target="_blank" rel="license noopener noreferrer" style="display:inline-block;">CC BY-NC 4.0<img style="height:22px!important;margin-left:3px;vertical-align:text-bottom;" src="https://mirrors.creativecommons.org/presskit/icons/cc.svg?ref=chooser-v1" alt=""><img style="height:22px!important;margin-left:3px;vertical-align:text-bottom;" src="https://mirrors.creativecommons.org/presskit/icons/by.svg?ref=chooser-v1" alt=""><img style="height:22px!important;margin-left:3px;vertical-align:text-bottom;" src="https://mirrors.creativecommons.org/presskit/icons/nc.svg?ref=chooser-v1" alt=""></a></p> 
