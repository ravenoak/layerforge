# LayerForge

[![Build Documentation using MkDocs](https://github.com/ravenoak/layerforge/actions/workflows/docs.yaml/badge.svg)](https://github.com/ravenoak/layerforge/actions/workflows/docs.yaml)

## Description

A 3D Model Slicing and SVG Generation Application

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [Features](#features)
- [Configuration](#configuration)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

<!-- - [Acknowledgements](#acknowledgements) -->

## Installation

1. Ensure Python 3.12 or newer is installed.
2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```
3. Install LayerForge and its dependencies:
   ```bash
   pip install -e .
   ```
   Alternatively, run `pip install -r requirements.txt` if you only need the runtime dependencies.

## Usage

Run the CLI to slice an STL model and produce SVGs:

```bash
layerforge --stl-file model.stl --layer-height 3.0 --output-folder output
```

Optional flags let you scale the model and control marker placement. Use `layerforge --help` for all options.

## Features

- Slice STL models into individual layers.
- Generate SVG files with contours, slice numbers and reference marks.
- Reference marks are chosen using a geometric stability metric inspired by GDOP.
- Marks inherit shape and position between adjacent slices and are adjusted to avoid overlaps.
- Supports multiple mark shapes (circle, square, triangle, arrow) for easy identification.
- Pyoxidizer packaging enables simple cross-platform distribution.

## Configuration

The CLI exposes parameters for tuning reference mark generation:

- `--mark-tolerance` – distance used when matching an existing mark. Defaults to `10.0`.
- `--mark-min-distance` – minimum distance from contours and between marks. Defaults to `10.0`.
- `--available-shapes` – comma separated list of shapes to cycle through when creating marks. Defaults to `circle,square,triangle,arrow`.

See [docs/configuration.md](docs/configuration.md) for full details on how these
options influence mark placement.

## Contributing

## License

This project is licensed under the Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0) License
for non-commercial use. For commercial use, please contact Caitlyn O'Hanna at caitlyn.ohanna@gmail.com to
obtain a commercial license.

For more details, see the [LICENSE](LICENSE) file for non-commercial use and
the [COMMERCIAL_LICENSE](COMMERCIAL_LICENSE) file for commercial use.

## Contact

For questions, comments, or concerns, please contact Caitlyn O'Hanna at caitlyn.ohanna@gmail.com.

<p><a property="dct:title" rel="cc:attributionURL" href="https://github.com/ravenoak/layerforge">LayerForge</a> by <a rel="cc:attributionURL dct:creator" property="cc:attributionName" href="https://github.com/ravenoak">Caitlyn O'Hanna</a> is licensed under <a href="https://creativecommons.org/licenses/by-nc/4.0/?ref=chooser-v1" target="_blank" rel="license noopener noreferrer" style="display:inline-block;">CC BY-NC 4.0<img style="height:22px!important;margin-left:3px;vertical-align:text-bottom;" src="https://mirrors.creativecommons.org/presskit/icons/cc.svg?ref=chooser-v1" alt=""><img style="height:22px!important;margin-left:3px;vertical-align:text-bottom;" src="https://mirrors.creativecommons.org/presskit/icons/by.svg?ref=chooser-v1" alt=""><img style="height:22px!important;margin-left:3px;vertical-align:text-bottom;" src="https://mirrors.creativecommons.org/presskit/icons/nc.svg?ref=chooser-v1" alt=""></a></p> 
