from typing import List

from layerforge.utils.optional_dependencies import require_module

trimesh = require_module("trimesh", "TrimeshLoader")

from layerforge.models.loading.base import MeshLoader
from layerforge.models.loading.mesh import Mesh


class TrimeshLoader(MeshLoader):
    """Loader for trimesh library."""

    def load_mesh(self, model_file: str) -> Mesh:
        """Load a mesh from a file using the trimesh library.

        Parameters
        ----------
        model_file : str
            Path to the model file.

        Returns
        -------
        Mesh
            The loaded mesh.
        """
        # TODO: Investigate encapsulating mesh in a custom object to abstract the specific library that is used.
        mesh = trimesh.load_mesh(model_file)
        if isinstance(mesh, list):
            raise ValueError(
                f"File '{model_file}' contains {len(mesh)} geometries; only a single mesh is supported."
            )
        return Mesh(mesh)
