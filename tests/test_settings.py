from pathlib import Path

import click
import pytest

from layerforge.settings import load_settings


def _write(tmp_path: Path, text: str, name: str = "layerforge.toml") -> Path:
    path = tmp_path / name
    path.write_text(text)
    return path


def test_defaults_without_a_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    s = load_settings(None, {})

    assert s.layer_height == 3.0
    assert s.marks.size is None
    assert s.marks.tolerance == 10.0
    assert s.marks.min_distance == 10.0
    assert s.marks.shapes == ["circle", "square", "triangle", "arrow"]
    assert s.marks.angle == 0.0


def test_precedence_is_command_line_then_file_then_default(tmp_path):
    cfg = _write(tmp_path, "layer_height = 2\n[marks]\ntolerance = 4\nmin_distance = 6\n")

    s = load_settings(cfg, {"mark_tolerance": 1.0, "mark_min_distance": None})

    assert s.marks.tolerance == 1.0  # command line
    assert s.marks.min_distance == 6.0  # file, because the option was not given
    assert s.layer_height == 2.0  # file
    assert s.marks.angle == 0.0  # default


def test_a_layerforge_toml_in_the_current_directory_is_read(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write(tmp_path, "layer_height = 2.5\n")

    assert load_settings(None, {}).layer_height == 2.5


def test_config_option_wins_over_the_file_in_the_current_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write(tmp_path, "layer_height = 2.5\n")
    other = _write(tmp_path, "layer_height = 1.5\n", name="other.toml")

    assert load_settings(other, {}).layer_height == 1.5


def test_all_keys_are_read(tmp_path):
    cfg = _write(
        tmp_path,
        "layer_height = 2\n[marks]\nsize = 4\ntolerance = 1\nmin_distance = 2\n"
        'shapes = ["circle", "arrow"]\nangle = 90\n',
    )

    s = load_settings(cfg, {})

    assert (s.layer_height, s.marks.size, s.marks.tolerance, s.marks.min_distance) == (
        2.0,
        4.0,
        1.0,
        2.0,
    )
    assert s.marks.shapes == ["circle", "arrow"]
    assert s.marks.angle == 90.0


@pytest.mark.parametrize(
    ("text", "key", "reason"),
    [
        ('[marks]\ncolour = "red"\n', "marks.colour", "Extra inputs"),
        ("kerf = 0.3\n", "kerf", "Extra inputs"),
        ('layer_height = "3"\n', "layer_height", "valid number"),
        ('[marks]\nshapes = "circle"\n', "marks.shapes", "valid list"),
        ("layer_height = 0\n", "layer_height", "must be > 0"),
        ("[marks]\ntolerance = -1\n", "marks.tolerance", "must be >= 0"),
        ("[marks]\nmin_distance = -1\n", "marks.min_distance", "must be >= 0"),
        ("[marks]\nsize = 0\n", "marks.size", "must be > 0"),
        ("[marks]\ntolerance = nan\n", "marks.tolerance", "must be a finite number"),
        ("[marks]\nangle = inf\n", "marks.angle", "must be a finite number"),
        ('[marks]\nshapes = ["hexagon"]\n', "marks.shapes", "unknown shape hexagon"),
        ("[marks]\nshapes = []\n", "marks.shapes", "must name at least one shape"),
    ],
)
def test_a_bad_file_names_the_file_and_the_key(tmp_path, text, key, reason):
    cfg = _write(tmp_path, text)

    with pytest.raises(click.UsageError) as excinfo:
        load_settings(cfg, {})

    message = excinfo.value.message
    assert message.startswith(f"{cfg}: {key}: ")
    assert reason in message


def test_a_toml_syntax_error_names_the_file(tmp_path):
    cfg = _write(tmp_path, "layer_height = \n")

    with pytest.raises(click.UsageError) as excinfo:
        load_settings(cfg, {})

    assert excinfo.value.message.startswith(f"{cfg}: ")


def test_an_unreadable_file_names_the_file(tmp_path):
    missing = tmp_path / "nope.toml"

    with pytest.raises(click.UsageError) as excinfo:
        load_settings(missing, {})

    assert excinfo.value.message.startswith(f"{missing}: ")


def test_a_bad_file_value_fails_even_when_the_command_line_overrides_it(tmp_path):
    cfg = _write(tmp_path, "[marks]\ntolerance = -1\n")

    with pytest.raises(click.UsageError, match="marks.tolerance"):
        load_settings(cfg, {"mark_tolerance": 1.0})


@pytest.mark.parametrize(
    ("option", "value", "hint", "reason"),
    [
        ("layer_height", 0.0, "--layer-height", "must be > 0"),
        ("mark_size", 0.0, "--mark-size", "must be > 0"),
        ("mark_size", float("nan"), "--mark-size", "must be a finite number"),
        ("mark_tolerance", -1.0, "--mark-tolerance", "must be >= 0"),
        ("mark_min_distance", float("inf"), "--mark-min-distance", "must be a finite number"),
        ("mark_angle", float("nan"), "--mark-angle", "must be a finite number"),
        ("available_shapes", [], "--available-shapes", "must name at least one shape"),
        ("available_shapes", ["hexagon"], "--available-shapes", "unknown shape hexagon"),
    ],
)
def test_a_bad_command_line_value_names_the_option_not_the_file(
    tmp_path, option, value, hint, reason
):
    cfg = _write(tmp_path, "[marks]\ntolerance = 4\n")

    with pytest.raises(click.BadParameter) as excinfo:
        load_settings(cfg, {option: value})

    assert excinfo.value.param_hint == hint
    assert reason in excinfo.value.message
