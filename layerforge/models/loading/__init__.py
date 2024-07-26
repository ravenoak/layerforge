__all__ = ['LoaderFactory', 'TrimeshLoader']

from .implementations.trimesh_loader import TrimeshLoader


class LoaderFactory:
    """Factory class for creating loaders

    This class is used to create loaders for different file formats.

    Attributes
    ----------
    loaders : dict
        A dictionary of loaders, where the key is the name of the loader
        and the value is the loader class.
    """
    loaders = {}

    @classmethod
    def register_loader(cls, name: str, loader_cls: type) -> None:
        """Register a mesh loader class with the factory.

        Parameters
        ----------
        name : str
            The name of the mesh loader
        loader_cls : type
            The mesh loader class to register

        Returns
        -------
        None
        """
        cls.loaders[name] = loader_cls

    @classmethod
    def get_loader(cls, name: str) -> object:
        """Get a loader by name.

        Parameters
        ----------
        name : str
            The name of the mesh loader to get.

        Returns
        -------
        object
            An instance of the loader class with the given name.
        """
        loader_cls = cls.loaders.get(name)
        if not loader_cls:
            raise ValueError(f"Loader not found for name: {name}")
        return loader_cls()
