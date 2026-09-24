from abc import ABC, abstractmethod

from .mesh import Mesh


class MeshLoader(ABC):
    """Base class for loading mesh files"""
    @abstractmethod
    def load_mesh(self, model_file: str) -> Mesh:
        """Load a mesh file

        Parameters
        ----------
        model_file : str
            Path to the model file to load

        Returns
        -------
        Mesh
            The loaded mesh.
        """
        pass
