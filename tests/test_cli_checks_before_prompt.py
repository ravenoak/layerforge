"""Every check of the command line and the config file runs before the ``--stl-file`` prompt.

#119 moved the config file check ahead of the prompt. #135 does the same for every other
check, and #136 makes ``--help`` win over a bad config file.
"""

import os
import tomllib

import click
import pytest
from click.testing import CliRunner

from layerforge import cli as cli_module
from layerforge.cli import ConflictingOptionsError, process_model

cli = cli_module.cli

BAD_FILE = "[marks]\ntolerance = -1\n"
BAD_FILE_MESSAGE = "bad.toml: marks.tolerance: must be >= 0"


@pytest.mark.parametrize(
    ("args", "exit_code", "message"),
    [
        (["--layer-height", "-1"], 2, "Invalid value for --layer-height: must be > 0"),
        (["--layer-height", "0"], 2, "Invalid value for --layer-height: must be > 0"),
        (["--layer-height", "nan"], 2, "Invalid value for --layer-height: must be a finite"),
        (["--layer-height", "inf"], 2, "Invalid value for --layer-height: must be a finite"),
        (["--mark-size", "0"], 2, "Invalid value for --mark-size: must be > 0"),
        (["--mark-size", "nan"], 2, "Invalid value for --mark-size: must be a finite"),
        (["--mark-tolerance", "-1"], 2, "Invalid value for --mark-tolerance: must be >= 0"),
        (["--mark-min-distance", "-1"], 2, "Invalid value for --mark-min-distance: must be >= 0"),
        (["--mark-angle", "nan"], 2, "Invalid value for --mark-angle: must be a finite"),
        (["--kerf", "-1"], 2, "Invalid value for --kerf: must be >= 0"),
        (["--kerf", "nan"], 2, "Invalid value for --kerf: must be a finite"),
        (["--kerf", "inf"], 2, "Invalid value for --kerf: must be a finite"),
        (["--kerf", "-inf"], 2, "Invalid value for --kerf: must be a finite"),
        (["--units", "ft"], 2, "Invalid value for '--units'"),
        (
            ["--cut-color", "notacolor"],
            2,
            "Invalid value for --cut-color: 'notacolor' is not a colour",
        ),
        (["--cut-color", ""], 2, "Invalid value for --cut-color: '' is not a colour"),
        (["--cut-color", "none"], 2, "Invalid value for --cut-color: 'none' is not a colour"),
        (["--cut-color", "Red"], 2, "Invalid value for --cut-color: 'Red' is not a colour"),
        (
            ["--engrave-color", "currentColor"],
            2,
            "Invalid value for --engrave-color: 'currentColor' is not a colour",
        ),
        (
            ["--engrave-color", "rgb(1,2)"],
            2,
            "Invalid value for --engrave-color: 'rgb(1,2)' is not a colour",
        ),
        (["--mark-color", "red"], 2, "No such option '--mark-color'"),
        (["--available-shapes", "hexagon"], 2, "Invalid value for --available-shapes: unknown"),
        (["--scale-factor", "0"], 2, "Invalid value for --scale-factor: must be > 0"),
        (["--scale-factor", "nan"], 2, "Invalid value for --scale-factor: must be a finite"),
        (["--target-height", "-1"], 2, "Invalid value for --target-height: must be > 0"),
        (["--target-height", "inf"], 2, "Invalid value for --target-height: must be a finite"),
        (
            ["--scale-factor", "1", "--target-height", "2"],
            1,
            "Only one of scale_factor or target_height can be provided.",
        ),
    ],
)
def test_cli_bad_option_is_reported_before_the_stl_prompt(args, exit_code, message):
    result = CliRunner().invoke(cli, args, input="box.stl\n")

    assert result.exit_code == exit_code, result.output
    assert message in result.output
    assert "STL file path" not in result.output


@pytest.mark.parametrize("colour", ["red", "#f00", "rgb(255,0,0)"])
def test_cli_accepts_the_colours_that_svg_reads(tmp_path, colour):
    result = CliRunner().invoke(
        cli,
        ["--cut-color", colour, "--engrave-color", colour, "--output-folder", str(tmp_path / "o")],
        input="\n",
    )

    assert "is not a colour" not in result.output
    assert "STL file path" in result.output  # every check passed, so the prompt came


def test_cli_bad_colour_in_the_file_is_reported_before_the_stl_prompt(tmp_path):
    bad = tmp_path / "bad.toml"
    bad.write_text('[output]\ncut_color = "none"\n')

    result = CliRunner().invoke(cli, ["--config", str(bad)], input="box.stl\n")

    assert result.exit_code == 2, result.output
    assert f"{bad}: output.cut_color: 'none' is not a colour" in result.output
    assert "STL file path" not in result.output


@pytest.mark.parametrize(
    ("cut", "engrave", "hint"),
    [("notacolor", None, "--cut-color"), (None, "notacolor", "--engrave-color")],
)
def test_process_model_bad_colour_is_reported_before_any_work(
    cylinder_stl, tmp_path, cut, engrave, hint
):
    """The Python API makes the same check as the command (#145)."""
    with pytest.raises(click.BadParameter) as excinfo:
        process_model(
            stl_file=str(cylinder_stl),
            output_folder=str(tmp_path / "out"),
            cut_color=cut,
            engrave_color=engrave,
        )
    assert excinfo.value.param_hint == hint
    assert "'notacolor' is not a colour" in excinfo.value.message
    assert not (tmp_path / "out").exists()


@pytest.mark.parametrize("below", [False, True])
def test_cli_output_folder_that_is_a_file_is_reported_before_the_stl_prompt(tmp_path, below):
    """The folder is a file, or would have to be made inside a file: both fail at mkdir."""
    a_file = tmp_path / "not_a_folder"
    a_file.write_text("x")
    folder = a_file / "sub" if below else a_file

    result = CliRunner().invoke(cli, ["--output-folder", str(folder)], input="box.stl\n")

    assert result.exit_code == 2, result.output
    assert "Invalid value for --output-folder" in result.output
    assert "STL file path" not in result.output


def test_cli_asks_for_the_stl_path_when_every_check_passes(cylinder_stl, tmp_path):
    out = tmp_path / "out"

    result = CliRunner().invoke(cli, ["--output-folder", str(out)], input=f"{cylinder_stl}\n")

    assert result.exit_code == 0, result.output
    assert "STL file path" in result.output
    assert list(out.glob("*.svg"))


def test_cli_ends_when_the_stl_prompt_gets_no_answer(tmp_path):
    result = CliRunner().invoke(cli, ["--output-folder", str(tmp_path / "out")], input="")

    assert result.exit_code == 1
    assert "Aborted" in result.output


def test_cli_bad_file_comes_before_the_scale_and_target_conflict(tmp_path):
    bad = tmp_path / "bad.toml"
    bad.write_text(BAD_FILE)

    result = CliRunner().invoke(
        cli, ["--config", str(bad), "--scale-factor", "1", "--target-height", "2"]
    )

    assert result.exit_code == 2
    assert "bad.toml: marks.tolerance: must be >= 0" in result.output


def test_cli_conflict_comes_before_a_bad_value():
    result = CliRunner().invoke(
        cli, ["--scale-factor", "1", "--target-height", "2", "--layer-height", "nan"]
    )

    assert result.exit_code == 1
    assert "Only one of scale_factor or target_height can be provided." in result.output


def test_process_model_bad_file_comes_before_the_conflict(cylinder_stl, tmp_path):
    """The Python API checks in the order the command does (#136)."""
    bad = tmp_path / "bad.toml"
    bad.write_text(BAD_FILE)

    with pytest.raises(Exception, match=BAD_FILE_MESSAGE) as caught:
        process_model(
            stl_file=str(cylinder_stl),
            output_folder=str(tmp_path / "out"),
            config_path=bad,
            scale_factor=1.0,
            target_height=2.0,
        )
    assert not isinstance(caught.value, ConflictingOptionsError)


def test_process_model_conflict_comes_before_a_bad_value(cylinder_stl, tmp_path):
    with pytest.raises(ConflictingOptionsError):
        process_model(
            stl_file=str(cylinder_stl),
            output_folder=str(tmp_path / "out"),
            layer_height=float("nan"),
            scale_factor=1.0,
            target_height=2.0,
        )


@pytest.mark.parametrize("via", ["config option", "discovered file"])
def test_cli_reads_the_config_file_once(cylinder_stl, tmp_path, monkeypatch, via):
    """The checked file is the file used, so an edit between two reads cannot matter (#136)."""
    settings_file = (
        tmp_path / "layerforge.toml" if via == "discovered file" else tmp_path / "s.toml"
    )
    settings_file.write_text("layer_height = 4.5\n")
    args = ["--stl-file", str(cylinder_stl), "--output-folder", str(tmp_path / "out")]
    if via == "config option":
        args += ["--config", str(settings_file)]
    else:
        monkeypatch.chdir(tmp_path)
    reads = []
    real_load = tomllib.load

    def counting_load(handle):
        reads.append(handle.name)
        return real_load(handle)

    monkeypatch.setattr(tomllib, "load", counting_load)

    result = CliRunner().invoke(cli, args)

    assert result.exit_code == 0, result.output
    assert len(reads) == 1


@pytest.mark.parametrize("order", [["--config", "{f}", "--help"], ["--help", "--config", "{f}"]])
def test_cli_help_wins_over_a_bad_config_file(tmp_path, order):
    bad = tmp_path / "bad.toml"
    bad.write_text(BAD_FILE)

    result = CliRunner().invoke(cli, [a.replace("{f}", str(bad)) for a in order])

    assert result.exit_code == 0, result.output
    assert "Usage:" in result.output
    assert "Using settings" not in result.output + result.stderr


def test_cli_help_does_not_name_a_good_config_file(tmp_path):
    good = tmp_path / "good.toml"
    good.write_text("layer_height = 2\n")

    result = CliRunner().invoke(cli, ["--config", str(good), "--help"])

    assert result.exit_code == 0, result.output
    assert "Using settings" not in result.output + result.stderr


def test_cli_output_folder_that_is_a_dangling_symlink_is_reported_before_the_stl_prompt(tmp_path):
    """``Path.exists`` is False for a broken link, but ``mkdir`` still fails on it."""
    link = tmp_path / "out"
    link.symlink_to(tmp_path / "missing")

    result = CliRunner().invoke(cli, ["--output-folder", str(link)], input="box.stl\n")

    assert result.exit_code == 2, result.output
    assert "Invalid value for --output-folder" in result.output
    assert "STL file path" not in result.output


@pytest.mark.parametrize(
    "args",
    [["--layer-height", "-1"], ["--scale-factor", "1", "--target-height", "2"]],
)
def test_cli_names_a_config_file_even_when_a_later_check_fails(tmp_path, monkeypatch, args):
    """A stray file must not go unnamed on a run that fails after it was read (#118)."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "layerforge.toml").write_text("layer_height = 2\n")

    result = CliRunner().invoke(cli, args)

    assert result.exit_code != 0
    assert "Using settings from layerforge.toml" in result.stderr


# Root can write to a read-only folder, and Windows has no such mode (and no geteuid).
needs_permission_checks = pytest.mark.skipif(
    getattr(os, "geteuid", lambda: 0)() == 0, reason="the process can write to a mode 555 folder"
)


@pytest.fixture
def read_only_folder(tmp_path):
    """A folder with mode 555. The mode is restored, so pytest can remove it."""
    folder = tmp_path / "ro"
    folder.mkdir()
    folder.chmod(0o555)
    yield folder
    folder.chmod(0o755)


def _assert_output_folder_refused_before_the_prompt(folder):
    result = CliRunner().invoke(cli, ["--output-folder", str(folder)], input="box.stl\n")

    assert result.exit_code == 2, result.output
    assert "Invalid value for --output-folder" in result.output
    assert "STL file path" not in result.output
    assert "Traceback" not in result.output


@pytest.mark.parametrize("text", ["", "  "])
def test_cli_empty_output_folder_is_reported_before_the_stl_prompt(text):
    """An empty name would write to the root: the first file would be ``/slice_000.svg``."""
    _assert_output_folder_refused_before_the_prompt(text)


@needs_permission_checks
@pytest.mark.parametrize("below", ["", "new", "new/deeper"])
def test_cli_output_folder_that_cannot_be_written_is_reported_before_the_stl_prompt(
    read_only_folder, below
):
    """An existing read-only folder, and a new folder at any depth under one."""
    _assert_output_folder_refused_before_the_prompt(read_only_folder / below)


def test_cli_output_folder_check_leaves_nothing_behind(tmp_path):
    new = tmp_path / "a" / "b"
    existing = tmp_path / "existing"
    existing.mkdir()

    for folder in (new, existing):
        result = CliRunner().invoke(
            cli, ["--stl-file", str(tmp_path / "nope.stl"), "--output-folder", str(folder)]
        )
        assert "Cannot load" in result.output  # the output folder check passed

    assert not (tmp_path / "a").exists()
    assert list(existing.iterdir()) == []


def test_cli_output_folder_name_that_is_too_long_is_reported_before_the_stl_prompt(tmp_path):
    """``lexists`` hides ``File name too long`` as "does not exist", and ``mkdir`` then fails."""
    _assert_output_folder_refused_before_the_prompt(tmp_path / ("a" * 300))


def test_cli_output_folder_with_a_null_byte_is_reported_before_the_stl_prompt(tmp_path):
    """``Path.lstat`` raises ``ValueError``, not ``OSError``, for it. ``lexists`` hid that."""
    _assert_output_folder_refused_before_the_prompt(str(tmp_path / "a\0b"))
