import pytest
pytest.importorskip("trimesh")

import trimesh
from layerforge.models.model_factory import ModelFactory
from layerforge.models.loading.base import MeshLoader


class DummyLoader(MeshLoader):
    def __init__(self, mesh):
        self.mesh = mesh

    def load_mesh(self, model_file: str):
        # return a copy to avoid modifying original
        return self.mesh.copy()


def test_scale_mesh_by_factor():
    mesh = trimesh.creation.box(extents=(1, 1, 1))
    scaled = ModelFactory._scale_mesh(mesh.copy(), scale_factor=2)
    assert pytest.approx(scaled.extents.tolist()) == [2.0, 2.0, 2.0]


def test_scale_mesh_by_target_height():
    mesh = trimesh.creation.box(extents=(1, 1, 1))
    scaled = ModelFactory._scale_mesh(mesh.copy(), target_height=5)
    assert pytest.approx(scaled.bounds[1][2] - scaled.bounds[0][2]) == 5.0


def test_scale_mesh_conflict():
    mesh = trimesh.creation.box(extents=(1, 1, 1))
    with pytest.raises(ValueError):
        ModelFactory._scale_mesh(mesh, scale_factor=1, target_height=2)


def test_calculate_origin():
    mesh = trimesh.creation.box(extents=(1, 2, 3))
    mesh.apply_translation([1, 2, 3])
    origin = ModelFactory._calculate_origin(mesh)
    assert pytest.approx(origin) == (1.0, 2.0)
