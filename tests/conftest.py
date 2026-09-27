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


@pytest.fixture
def sheared_cylinder_stl(tmp_path):
    """Radius 20, height 60, sheared 0.5 in x per unit z (#107's own evidence)."""
    import numpy as np

    mesh = trimesh.creation.cylinder(radius=20.0, height=60.0, sections=48)
    shear = np.eye(4)
    shear[0, 2] = 0.5  # x += 0.5 * z
    mesh.apply_transform(shear)
    path = tmp_path / "sheared_cylinder.stl"
    mesh.export(path)
    return path
