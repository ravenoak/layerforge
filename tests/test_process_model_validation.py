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


@pytest.mark.parametrize(
    ("tolerance", "min_distance", "hint"),
    [(-1.0, 10.0, "--mark-tolerance"), (10.0, -1.0, "--mark-min-distance")],
)
def test_process_model_negative_mark_option_fails_before_slicing(
    cylinder_stl, tmp_path, tolerance, min_distance, hint
):
    out = tmp_path / "out"
    with pytest.raises(click.BadParameter) as excinfo:
        process_model(
            stl_file=str(cylinder_stl),
            layer_height=1.0,
            output_folder=str(out),
            mark_tolerance=tolerance,
            mark_min_distance=min_distance,
        )
    assert excinfo.value.param_hint == hint
    assert not out.exists()


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
@pytest.mark.parametrize(
    ("option", "hint"),
    [
        ("layer_height", "--layer-height"),
        ("scale_factor", "--scale-factor"),
        ("target_height", "--target-height"),
        ("mark_tolerance", "--mark-tolerance"),
        ("mark_min_distance", "--mark-min-distance"),
        ("mark_angle", "--mark-angle"),
    ],
)
def test_process_model_non_finite_option_fails_before_slicing(
    cylinder_stl, tmp_path, option, hint, value
):
    out = tmp_path / "out"
    kwargs = {"layer_height": 1.0, option: value}
    with pytest.raises(click.BadParameter) as excinfo:
        process_model(stl_file=str(cylinder_stl), output_folder=str(out), **kwargs)
    assert excinfo.value.param_hint == hint
    assert "finite" in excinfo.value.message
    assert not out.exists()
