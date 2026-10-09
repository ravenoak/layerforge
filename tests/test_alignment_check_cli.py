"""The command checks every pair of adjacent layers before it writes (TR-2, TR-12, #92)."""

import logging

import click
import pytest
import trimesh
from click.testing import CliRunner

from layerforge.cli import cli, process_model


def _stl(tmp_path, mesh, name):
    path = tmp_path / f"{name}.stl"
    mesh.export(path)
    return path


@pytest.fixture
def cube_stl(tmp_path):
    return _stl(tmp_path, trimesh.creation.box(extents=(20, 20, 20)), "cube")


@pytest.fixture
def cone_stl(tmp_path):
    return _stl(tmp_path, trimesh.creation.cone(radius=20, height=30), "cone")


def _invoke(stl, out, *extra):
    return CliRunner().invoke(cli, ["--stl-file", str(stl), "--output-folder", str(out), *extra])


def test_an_aligned_stack_is_written_and_exits_0(cube_stl, tmp_path):
    out = tmp_path / "out"
    result = _invoke(cube_stl, out)
    assert result.exit_code == 0, result.stderr
    assert len(list(out.glob("slice_*.svg"))) == 7
    assert "Nothing was written" not in result.stderr


def test_a_stack_with_pairs_that_share_no_mark_writes_nothing_and_exits_1(cone_stl, tmp_path):
    out = tmp_path / "out"
    result = _invoke(cone_stl, out)
    assert result.exit_code == 1
    assert not out.exists()
    assert "Traceback" not in result.stderr
    assert "slices 7 and 8 (piece 0 and piece 0): the pieces share no mark" in result.stderr
    assert "slices 8 and 9 (piece 0 and piece 0): the pieces share no mark" in result.stderr
    assert result.stderr.count("the pieces share no mark") == 2  # every failure, not the first
    assert "Nothing was written. Use --allow-unaligned" in result.stderr


def test_allow_unaligned_writes_every_file_and_warns_once_per_failure(cone_stl, tmp_path, caplog):
    out = tmp_path / "out"
    with caplog.at_level(logging.WARNING):
        result = _invoke(cone_stl, out, "--allow-unaligned")
    assert result.exit_code == 0, result.stderr
    assert len(list(out.glob("slice_*.svg"))) == 10
    messages = [r.getMessage() for r in caplog.records if "share no mark" in r.getMessage()]
    assert len(messages) == 2


def test_the_config_file_can_allow_it(cone_stl, tmp_path):
    config = tmp_path / "allow.toml"
    config.write_text("[checks]\nallow_unaligned = true\n")
    out = tmp_path / "out"
    result = _invoke(cone_stl, out, "--config", str(config))
    assert result.exit_code == 0, result.stderr
    assert len(list(out.glob("slice_*.svg"))) == 10


def test_a_list_with_no_shape_that_has_a_direction_fails_every_pair(cube_stl, tmp_path):
    out = tmp_path / "out"
    result = _invoke(cube_stl, out, "--available-shapes", "circle")
    assert result.exit_code == 1
    assert not out.exists()
    assert result.stderr.count("look the same after a turn") == 6  # 7 slices, 6 pairs


def test_a_model_of_one_layer_passes_without_a_message(tmp_path):
    plate = _stl(tmp_path, trimesh.creation.box(extents=(40, 40, 2)), "plate")
    out = tmp_path / "out"
    result = _invoke(plate, out)
    assert result.exit_code == 0, result.stderr
    assert len(list(out.glob("slice_*.svg"))) == 1
    assert "share no mark" not in result.stderr
    assert "Nothing was written" not in result.stderr


def test_a_mark_tolerance_of_zero_does_not_end_in_a_traceback(cube_stl, tmp_path):
    out = tmp_path / "out"
    result = _invoke(cube_stl, out, "--mark-tolerance", "0")
    assert result.exit_code == 0, result.stderr
    assert "Traceback" not in result.stderr


def test_process_model_takes_allow_unaligned_too(cone_stl, tmp_path):
    out = tmp_path / "out"
    with pytest.raises(click.ClickException):
        process_model(stl_file=str(cone_stl), output_folder=str(out))
    assert not out.exists()
    process_model(stl_file=str(cone_stl), output_folder=str(out), allow_unaligned=True)
    assert len(list(out.glob("slice_*.svg"))) == 10
