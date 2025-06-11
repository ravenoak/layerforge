from abc import ABC, abstractmethod


class MeshLoader(ABC):
    """Base class for loading mesh files"""
    @abstractmethod
    def load_mesh(self, model_file: str) -> object:
        """Load a mesh file

        Parameters
        ----------
        model_file : str
            Path to the model file to load

        Returns
        -------
        object
            The loaded mesh. Type depends on the implementation.
        """
        pass
