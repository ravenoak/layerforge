import click
import pytest

from layerforge.cli import process_model


def test_process_model_invalid_layer_height(cylinder_stl, tmp_path):
    with pytest.raises(click.BadParameter):
        process_model(
            stl_file=str(cylinder_stl),
            layer_height=0,
            output_folder=str(tmp_path),
        )


def test_process_model_invalid_scale_factor(cylinder_stl, tmp_path):
    with pytest.raises(click.BadParameter):
        process_model(
            stl_file=str(cylinder_stl),
            layer_height=1.0,
            output_folder=str(tmp_path),
            scale_factor=0,
        )


def test_process_model_invalid_target_height(cylinder_stl, tmp_path):
    with pytest.raises(click.BadParameter):
        process_model(
            stl_file=str(cylinder_stl),
            layer_height=1.0,
            output_folder=str(tmp_path),
            target_height=0,
        )


@pytest.fixture
def flat_stl(tmp_path):
    """A single triangle in the z=0 plane, so the mesh has no height."""
    trimesh = pytest.importorskip("trimesh")
    mesh = trimesh.Trimesh(vertices=[[0, 0, 0], [1, 0, 0], [0, 1, 0]], faces=[[0, 1, 2]])
    path = tmp_path / "flat.stl"
    mesh.export(path)
    return path


def test_process_model_zero_height_mesh_is_a_clear_error(flat_stl, tmp_path):
    with pytest.raises(click.ClickException, match="no height"):
        process_model(
            stl_file=str(flat_stl),
            layer_height=1.0,
            output_folder=str(tmp_path / "out"),
            target_height=10.0,
        )


def test_process_model_empty_mesh_file_is_a_clear_error(tmp_path):
    empty = tmp_path / "empty.stl"
    empty.write_text("this is not a mesh\n")
    with pytest.raises(click.ClickException, match="empty.stl"):
        process_model(
            stl_file=str(empty),
            layer_height=1.0,
            output_folder=str(tmp_path / "out"),
        )


def test_process_model_missing_file_is_a_clear_error(tmp_path):
    missing = tmp_path / "missing.stl"
    with pytest.raises(click.ClickException, match="missing.stl"):
        process_model(
            stl_file=str(missing),
            layer_height=1.0,
            output_folder=str(tmp_path / "out"),
        )


@pytest.mark.parametrize("shapes", ["circle,hexagon", ",", ""])
def test_process_model_bad_shapes_fail_before_slicing(cylinder_stl, tmp_path, shapes):
    out = tmp_path / "out"
    with pytest.raises(click.BadParameter) as excinfo:
        process_model(
            stl_file=str(cylinder_stl),
            layer_height=1.0,
            output_folder=str(out),
            available_shapes=shapes,
        )
    assert excinfo.value.param_hint == "--available-shapes"
    assert not out.exists()
