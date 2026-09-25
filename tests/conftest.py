import pytest

pytest.importorskip("trimesh")
import trimesh


@pytest.fixture(autouse=True)
def _empty_working_directory(monkeypatch, tmp_path_factory):
    """Run every test in an empty directory, so a ./layerforge.toml is never read (#120)."""
    monkeypatch.chdir(tmp_path_factory.mktemp("cwd"))


@pytest.fixture
def cylinder_stl(tmp_path):
    mesh = trimesh.creation.cylinder(radius=30.0, height=10.0)
    path = tmp_path / "cylinder.stl"
    mesh.export(path)
    return path
