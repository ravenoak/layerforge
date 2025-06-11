from click.testing import CliRunner
import pytest

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
    assert called["available_shapes"] == "circle,square,triangle,arrow"
    assert called["mark_angle"] == 0.0
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
