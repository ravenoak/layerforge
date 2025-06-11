import pytest

pytest.importorskip("trimesh")

from layerforge.utils.loader_initialization import initialize_loaders
from layerforge.models.loading import LoaderFactory
from layerforge.models.loading.implementations.trimesh_loader import TrimeshLoader


def test_initialize_loaders_registers_trimesh(monkeypatch):
    monkeypatch.setattr(LoaderFactory, "loaders", {}, raising=False)
    initialize_loaders()
    assert LoaderFactory.loaders["trimesh"] is TrimeshLoader
