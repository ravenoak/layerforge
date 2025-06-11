import pytest

from layerforge.models.loading import LoaderFactory
from layerforge.models.loading.base import MeshLoader


class DummyLoader(MeshLoader):
    def load_mesh(self, model_file: str):
        return model_file


def test_register_and_get_loader(monkeypatch):
    monkeypatch.setattr(LoaderFactory, "loaders", {}, raising=False)
    LoaderFactory.register_loader("dummy", DummyLoader)
    loader = LoaderFactory.get_loader("dummy")
    assert isinstance(loader, DummyLoader)


def test_get_unknown_loader(monkeypatch):
    monkeypatch.setattr(LoaderFactory, "loaders", {}, raising=False)
    with pytest.raises(ValueError):
        LoaderFactory.get_loader("missing")
