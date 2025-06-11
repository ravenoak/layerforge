from typing import List, Union

import trimesh

from src.layerforge.models.loading.base import MeshLoader


class TrimeshLoader(MeshLoader):
    """Loader for trimesh library."""
    def load_mesh(self, model_file: str) -> Union[trimesh.Geometry, List[trimesh.Geometry]]:
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
        # TODO: Research if it is appropriate to throw an exception here if a list of meshes is returned.
        return trimesh.load_mesh(model_file)
