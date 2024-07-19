__all__ = ['LoaderFactory', 'TrimeshLoader']

from .implementations.trimesh_loader import TrimeshLoader


class LoaderFactory:
    loaders = {}

    @classmethod
    def register_loader(cls, name, loader_cls):
        cls.loaders[name] = loader_cls

    @classmethod
    def get_loader(cls, name):
        loader_cls = cls.loaders.get(name)
        if not loader_cls:
            raise ValueError(f"Loader not found for name: {name}")
        return loader_cls()
