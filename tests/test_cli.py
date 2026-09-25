import math

import pytest
from click.testing import CliRunner

from layerforge import cli as cli_module

cli = cli_module.cli


def test_cli_delegates_to_process_model(monkeypatch):
    runner = CliRunner()
    called = {}

    def fake_process_model(**kwargs):
        called.update(kwargs)

    monkeypatch.setattr(cli_module, "process_model", fake_process_model)

    result = runner.invoke(
        cli,
        [
            "--stl-file",
            "model.stl",
            "--layer-height",
            "1.0",
            "--output-folder",
            "out",
            "--scale-factor",
            "2.0",
        ],
    )
    assert result.exit_code == 0
    assert called["stl_file"] == "model.stl"
    assert called["layer_height"] == 1.0
    assert called["output_folder"] == "out"
    assert called["scale_factor"] == 2.0
    assert called["target_height"] is None
    # Settings that can come from the config file are None until resolved.
    assert called["available_shapes"] is None
    assert called["mark_angle"] is None
    assert called["mark_size"] is None
    assert called["config_path"] is None
    assert called["mark_color"] is None


def test_cli_conflicting_options(monkeypatch):
    runner = CliRunner()

    result = runner.invoke(
        cli,
        [
            "--stl-file",
            "model.stl",
            "--layer-height",
            "0.5",
            "--output-folder",
            "out",
            "--scale-factor",
            "1.0",
            "--target-height",
            "10.0",
        ],
    )

    assert result.exit_code == 1
    assert "Only one of scale_factor or target_height can be provided." in result.output


def test_cli_invalid_options_error(cylinder_stl, tmp_path):
    """Invoking with both scaling options should produce an error."""
    runner = CliRunner()

    result = runner.invoke(
        cli,
        [
            "--stl-file",
            str(cylinder_stl),
            "--layer-height",
            "0.5",
            "--output-folder",
            str(tmp_path),
            "--scale-factor",
            "1.0",
            "--target-height",
            "10.0",
        ],
    )

    assert result.exit_code != 0
    assert "Only one of scale_factor or target_height can be provided." in result.output


@pytest.mark.parametrize("scale_factor", ["0", "-1", "nan", "inf", "2.0"])
def test_cli_scale_factor_with_target_height_is_a_conflict_for_every_value(
    cylinder_stl, tmp_path, scale_factor
):
    """Two options that cannot be used together fail the same way for any value (#117)."""
    result = CliRunner().invoke(
        cli,
        [
            "--stl-file",
            str(cylinder_stl),
            "--output-folder",
            str(tmp_path),
            "--scale-factor",
            scale_factor,
            "--target-height",
            "5",
        ],
    )

    assert result.exit_code == 1
    assert "Only one of scale_factor or target_height can be provided." in result.output


@pytest.mark.parametrize("option", ["--mark-tolerance", "--mark-min-distance"])
def test_cli_negative_mark_option_is_a_usage_error(cylinder_stl, tmp_path, option):
    """A negative mark option exits with usage code 2 and names the option."""
    runner = CliRunner()

    result = runner.invoke(
        cli,
        ["--stl-file", str(cylinder_stl), "--output-folder", str(tmp_path), option, "-1"],
    )

    assert result.exit_code == 2
    assert option in result.output


def test_cli_end_to_end_generates_svgs(tmp_path):
    """A full CLI run should generate SVG slices."""
    pytest.importorskip("trimesh")
    pytest.importorskip("svgwrite")
    pytest.importorskip("shapely")

    import trimesh

    mesh = trimesh.creation.box(extents=(20, 20, 20))
    stl_path = tmp_path / "model.stl"
    mesh.export(stl_path)

    out_dir = tmp_path / "svgs"
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "--stl-file",
            str(stl_path),
            "--layer-height",
            "5.0",
            "--output-folder",
            str(out_dir),
        ],
    )

    assert result.exit_code == 0, result.output
    assert sorted(out_dir.glob("slice_*.svg")), "no svg files generated"


def test_cli_invalid_layer_height(monkeypatch):
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "--stl-file",
            "model.stl",
            "--layer-height",
            "0",
            "--output-folder",
            "out",
        ],
    )
    assert result.exit_code != 0
    assert "Invalid value for --layer-height" in result.output


def test_cli_missing_stl_file_error(tmp_path):
    """Missing STL path should result in a non-zero exit code."""
    runner = CliRunner()
    out_dir = tmp_path / "out"
    result = runner.invoke(
        cli,
        [
            "--stl-file",
            str(tmp_path / "missing.stl"),
            "--layer-height",
            "1.0",
            "--output-folder",
            str(out_dir),
        ],
    )
    assert result.exit_code != 0
    assert result.exception is not None


@pytest.mark.parametrize("value", ["nan", "inf"])
@pytest.mark.parametrize(
    "option",
    ["--layer-height", "--mark-tolerance", "--mark-min-distance", "--mark-angle"],
)
def test_cli_non_finite_option_is_a_usage_error(cylinder_stl, tmp_path, option, value):
    """A nan or inf option exits with usage code 2 and names the option."""
    runner = CliRunner()

    result = runner.invoke(
        cli,
        ["--stl-file", str(cylinder_stl), "--output-folder", str(tmp_path), option, value],
    )

    assert result.exit_code == 2
    assert option in result.output


class _StopAfterSlicing(Exception):
    """Raised by the spy so a wiring test does not write files."""


@pytest.fixture
def sliced(monkeypatch, cylinder_stl, tmp_path):
    """Run the CLI up to slicing and return what ``slice_model`` received."""
    monkeypatch.chdir(tmp_path)
    seen = {}

    def spy(model, config=None):
        seen["layer_height"] = model.layer_height
        seen["config"] = config
        raise _StopAfterSlicing

    monkeypatch.setattr(cli_module.SlicerService, "slice_model", staticmethod(spy))

    def run(*args):
        result = CliRunner().invoke(cli, ["--stl-file", str(cylinder_stl), *args])
        assert isinstance(result.exception, _StopAfterSlicing), result.output
        return seen

    return run


def test_cli_defaults_reach_the_slicer(sliced):
    seen = sliced()

    assert seen["layer_height"] == 3.0
    cfg = seen["config"]
    assert (cfg.tolerance, cfg.min_distance, cfg.angle, cfg.size) == (10.0, 10.0, 0.0, None)
    assert cfg.available_shapes == ["circle", "square", "triangle", "arrow"]


def test_cli_config_file_values_reach_the_slicer(sliced, tmp_path):
    (tmp_path / "layerforge.toml").write_text(
        'layer_height = 2\n[marks]\nsize = 6\ntolerance = 4\nangle = 90\nshapes = ["arrow"]\n'
    )

    seen = sliced()

    assert seen["layer_height"] == 2.0
    cfg = seen["config"]
    assert cfg.size == 6.0
    assert cfg.tolerance == 4.0
    assert cfg.angle == pytest.approx(math.pi / 2)  # degrees in the file, radians inside
    assert cfg.available_shapes == ["arrow"]


def test_cli_option_beats_config_file(sliced, tmp_path):
    (tmp_path / "layerforge.toml").write_text(
        "layer_height = 2\n[marks]\ntolerance = 4\nmin_distance = 6\n"
    )

    seen = sliced("--layer-height", "1.5", "--mark-tolerance", "1", "--available-shapes", "circle")

    assert seen["layer_height"] == 1.5
    assert seen["config"].tolerance == 1.0
    assert seen["config"].min_distance == 6.0
    assert seen["config"].available_shapes == ["circle"]


def test_cli_config_option_names_the_file(sliced, tmp_path):
    other = tmp_path / "other.toml"
    other.write_text("layer_height = 1.25\n")

    assert sliced("--config", str(other))["layer_height"] == 1.25


def test_cli_mark_size_reaches_the_slicer(sliced):
    assert sliced("--mark-size", "7")["config"].size == 7.0


def test_cli_bad_config_file_stops_before_the_mesh_is_read(tmp_path, monkeypatch):
    """Exit 2 with a missing STL shows the settings were checked first."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "layerforge.toml").write_text("[marks]\ntolerance = -1\n")

    result = CliRunner().invoke(cli, ["--stl-file", "missing.stl"])

    assert result.exit_code == 2
    assert "layerforge.toml: marks.tolerance: must be >= 0" in result.output


def test_cli_bad_config_file_is_reported_before_the_stl_prompt(tmp_path, monkeypatch):
    """The person is not asked for a path when the settings file is already bad (#119)."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "layerforge.toml").write_text("[marks]\ntolerance = -1\n")

    result = CliRunner().invoke(cli, [], input="box.stl\n")

    assert result.exit_code == 2
    assert "layerforge.toml: marks.tolerance: must be >= 0" in result.output
    assert "STL file path" not in result.output


def test_cli_help_works_with_a_bad_config_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "layerforge.toml").write_text("[marks]\ntolerance = -1\n")

    result = CliRunner().invoke(cli, ["--help"])

    assert result.exit_code == 0
    assert "--config" in result.output


def test_cli_says_when_it_reads_a_discovered_config_file(cylinder_stl, tmp_path, monkeypatch):
    """A stray layerforge.toml must not change a run without a word (#118)."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "layerforge.toml").write_text("layer_height = 4.5\n")

    result = CliRunner().invoke(
        cli, ["--stl-file", str(cylinder_stl), "--output-folder", str(tmp_path / "out")]
    )

    assert result.exit_code == 0, result.output
    assert result.stderr.count("Using settings from layerforge.toml") == 1
    assert "Using settings" not in result.stdout


def test_cli_says_when_it_reads_the_config_option_file(cylinder_stl, tmp_path):
    other = tmp_path / "other.toml"
    other.write_text("layer_height = 4.5\n")

    result = CliRunner().invoke(
        cli,
        [
            "--stl-file",
            str(cylinder_stl),
            "--config",
            str(other),
            "--output-folder",
            str(tmp_path / "out"),
        ],
    )

    assert result.exit_code == 0, result.output
    assert result.stderr.count(f"Using settings from {other}") == 1
    assert "Using settings" not in result.stdout


def test_cli_says_nothing_about_settings_without_a_config_file(cylinder_stl, tmp_path):
    result = CliRunner().invoke(
        cli, ["--stl-file", str(cylinder_stl), "--output-folder", str(tmp_path / "out")]
    )

    assert result.exit_code == 0, result.output
    assert "Using settings" not in result.output


def test_cli_missing_config_file_is_a_usage_error(cylinder_stl, tmp_path):
    result = CliRunner().invoke(
        cli, ["--stl-file", str(cylinder_stl), "--config", str(tmp_path / "missing.toml")]
    )

    assert result.exit_code == 2
    assert "Invalid value for '--config'" in result.output
    assert "does not exist" in result.output


@pytest.mark.parametrize("value", ["0", "nan", "-1"])
def test_cli_bad_mark_size_is_a_usage_error(cylinder_stl, tmp_path, value):
    result = CliRunner().invoke(
        cli,
        ["--stl-file", str(cylinder_stl), "--output-folder", str(tmp_path), "--mark-size", value],
    )

    assert result.exit_code == 2
    assert "Invalid value for --mark-size" in result.output
