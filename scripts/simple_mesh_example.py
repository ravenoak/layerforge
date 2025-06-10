import tempfile
from pathlib import Path

import trimesh

from layerforge.cli import process_model


def run_example(output_folder: str = "example_output") -> None:
    """Generate a box mesh and slice it with :func:`process_model`."""
    mesh = trimesh.creation.box(extents=(20, 20, 20))
    with tempfile.NamedTemporaryFile(suffix=".stl", delete=False) as tmp:
        mesh.export(tmp.name)
        stl_path = tmp.name
    try:
        process_model(stl_file=stl_path, layer_height=5.0, output_folder=output_folder)
    finally:
        Path(stl_path).unlink(missing_ok=True)


if __name__ == "__main__":
    run_example()
