import pytest

pytest.importorskip("trimesh")

import trimesh
from layerforge.models.loading.implementations.trimesh_loader import TrimeshLoader


def test_trimesh_loader_multiple_mesh_error(monkeypatch):
    mesh1 = trimesh.creation.box()
    mesh2 = trimesh.creation.box()

    def fake_load_mesh(path):
        return [mesh1, mesh2]

    loader = TrimeshLoader()
    monkeypatch.setattr(trimesh, "load_mesh", fake_load_mesh)
    with pytest.raises(ValueError):
        loader.load_mesh("dummy.stl")
