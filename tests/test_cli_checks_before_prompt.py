"""Every check of the command line and the config file runs before the ``--stl-file`` prompt.

#119 moved the config file check ahead of the prompt. #135 does the same for every other
check, and #136 makes ``--help`` win over a bad config file.
"""

import pytest
from click.testing import CliRunner

from layerforge import cli as cli_module
from layerforge import settings as settings_module
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
        (["--units", "ft"], 2, "Invalid value for '--units'"),
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
    real_read = settings_module._read
    monkeypatch.setattr(
        settings_module, "_read", lambda path: reads.append(path) or real_read(path)
    )

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
