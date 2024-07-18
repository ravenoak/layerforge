from layerforge.models.loading import LoaderFactory
from layerforge.models.loading.implementations.trimesh_loader import TrimeshLoader


def initialize_loaders():
    LoaderFactory.register_loader("trimesh", TrimeshLoader)
