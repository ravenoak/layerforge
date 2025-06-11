from typing import List, Union

from layerforge.utils.optional_dependencies import require_module

trimesh = require_module("trimesh", "TrimeshLoader")

from layerforge.models.loading.base import MeshLoader


class TrimeshLoader(MeshLoader):
    """Loader for trimesh library."""

    def load_mesh(
        self, model_file: str
    ) -> Union[trimesh.Geometry, List[trimesh.Geometry]]:
        """Load a mesh from a file using the trimesh library.

        Parameters
        ----------
        model_file : str
            Path to the model file.

        Returns
        -------
        Union[Geometry, List[Geometry]]
            The loaded mesh or meshes.
        """
        # TODO: Investigate encapsulating mesh in a custom object to abstract the specific library that is used.
        mesh = trimesh.load_mesh(model_file)
        if isinstance(mesh, list):
            raise ValueError(
                f"File '{model_file}' contains {len(mesh)} geometries; only a single mesh is supported."
            )
        return mesh
