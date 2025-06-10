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
    assert called["available_shapes"] == "circle,square,triangle,arrow"


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
