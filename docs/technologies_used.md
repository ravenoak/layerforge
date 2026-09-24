# Technologies Used

## Overview

This project utilizes a variety of technologies to achieve its goals. Below is a detailed description of each technology
used.

## GitHub Actions

GitHub Actions is used for continuous integration and continuous deployment (CI/CD). It automates the build, test, and
deployment processes.

## mkdocs

mkdocs is used for project documentation. It helps create a static site from Markdown files, making it easy to maintain
and update documentation.

## uv

uv manages the Python version, the virtual environment, the lock file (`uv.lock`) and the package build.

## Python Libraries

### svgwrite

`svgwrite` is used for generating SVG files.

### trimesh

`trimesh` is used for loading and manipulating 3D models. It needs `scipy` and
`networkx` to cut a mesh into slices.

### shapely

`shapely` holds the slice outlines as polygons and answers the distance and
containment questions that place reference marks.

### pydantic

`pydantic` validates the reference mark settings (`ReferenceMarkConfig`).

## Additional Libraries

- `click`: Used for creating command-line interfaces.
- `pytest` and `hypothesis`: Used for testing the application.
- `ruff` and `pyright`: Used for linting, formatting and type checking.
- Allium (`allium check`): Checks the formal specification in `specs/`.
- `mkdocstrings-python`: Used for generating documentation from docstrings.