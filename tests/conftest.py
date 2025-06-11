import pytest
pytest.importorskip("trimesh")
import trimesh


@pytest.fixture
def cylinder_stl(tmp_path):
    mesh = trimesh.creation.cylinder(radius=30.0, height=10.0)
    path = tmp_path / "cylinder.stl"
    mesh.export(path)
    return path
