from pathlib import Path

import click
import pytest
from pydantic import model_validator

import layerforge.settings as settings_module
from layerforge.settings import load_settings


def _write(tmp_path: Path, text: str, name: str = "layerforge.toml") -> Path:
    path = tmp_path / name
    path.write_text(text)
    return path


def test_defaults_without_a_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    s = load_settings(None, {})

    assert s.layer_height == 3.0
    assert s.kerf == 0.3
    assert (s.marks.size, s.marks.tolerance, s.marks.min_distance) == (None, None, None)
    assert (s.marks.min_hole_ratio, s.marks.min_hole_kerf_factor) == (1.0, 1.5)
    assert s.marks.shapes == ["circle", "square", "triangle", "arrow"]
    assert s.marks.angle == 0.0
    assert s.marks.min_web_ratio == 0.5
    assert (s.output.cut_color, s.output.engrave_color) == ("red", "black")
    assert s.output.hairline_width == 0.01


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
        'shapes = ["circle", "arrow"]\nangle = 90\nmin_web_ratio = 0.75\n'
        "min_hole_ratio = 2\nmin_hole_kerf_factor = 3\n",
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
    assert s.marks.min_web_ratio == 0.75
    assert (s.marks.min_hole_ratio, s.marks.min_hole_kerf_factor) == (2.0, 3.0)


@pytest.mark.parametrize(
    ("text", "key", "reason"),
    [
        ('[marks]\ncolour = "red"\n', "marks.colour", "Extra inputs"),
        ("dowel = 1\n", "dowel", "Extra inputs"),
        ("kerf = -1\n", "kerf", "must be >= 0"),
        ("kerf = nan\n", "kerf", "must be a finite number"),
        ("[marks]\nmin_hole_ratio = 0\n", "marks.min_hole_ratio", "must be > 0"),
        ("[marks]\nmin_hole_ratio = inf\n", "marks.min_hole_ratio", "must be a finite number"),
        ("[marks]\nmin_hole_kerf_factor = -1\n", "marks.min_hole_kerf_factor", "must be >= 0"),
        ('layer_height = "3"\n', "layer_height", "valid number"),
        ('[marks]\nshapes = "circle"\n', "marks.shapes", "valid list"),
        ("layer_height = 0\n", "layer_height", "must be > 0"),
        ("[marks]\ntolerance = -1\n", "marks.tolerance", "must be >= 0"),
        ("[marks]\nmin_distance = -1\n", "marks.min_distance", "must be >= 0"),
        ("[marks]\nsize = 0\n", "marks.size", "must be > 0"),
        ("[marks]\nmin_web_ratio = -1\n", "marks.min_web_ratio", "must be >= 0"),
        ("[marks]\nmin_web_ratio = nan\n", "marks.min_web_ratio", "must be a finite number"),
        ("[marks]\ntolerance = nan\n", "marks.tolerance", "must be a finite number"),
        ("[marks]\nangle = inf\n", "marks.angle", "must be a finite number"),
        ('[marks]\nshapes = ["hexagon"]\n', "marks.shapes", "unknown shape hexagon"),
        ("[marks]\nshapes = []\n", "marks.shapes", "must name at least one shape"),
        ('units = "ft"\n', "units", "Input should be"),
        ("units = 5\n", "units", "Input should be"),
        ('[output]\ncut_color = "notacolor"\n', "output.cut_color", "'notacolor' is not a colour"),
        ('[output]\nengrave_color = ""\n', "output.engrave_color", "'' is not a colour"),
        ('[output]\ncut_color = "none"\n', "output.cut_color", "'none' is not a colour"),
        ('[output]\ncut_color = "currentColor"\n', "output.cut_color", "is not a colour"),
        ('[output]\ncut_color = "Red"\n', "output.cut_color", "'Red' is not a colour"),
        ('[output]\nengrave_color = "url(#a)"\n', "output.engrave_color", "is not a colour"),
        ("[output]\ncut_color = 5\n", "output.cut_color", "valid string"),
        ("[output]\nhairline_width = 0\n", "output.hairline_width", "must be > 0"),
        ("[output]\nhairline_width = -1\n", "output.hairline_width", "must be > 0"),
        ("[output]\nhairline_width = nan\n", "output.hairline_width", "must be a finite number"),
        ("[output]\nstroke = 1\n", "output.stroke", "Extra inputs"),
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


def test_a_bad_option_value_with_no_option_hint_is_a_usage_error_not_a_key_error(monkeypatch):
    """A key without an option (a later TR-16 key) must not end in a traceback (#121)."""
    monkeypatch.setattr(settings_module, "_OPTION_HINTS", {})

    with pytest.raises(click.UsageError, match=r"marks\.tolerance: must be >= 0"):
        load_settings(None, {"mark_tolerance": -1})


def test_a_check_across_keys_is_a_usage_error_that_names_settings(monkeypatch):
    """An error with no key of its own is still named, not printed as ': reason' (#121)."""

    class Crossed(settings_module.Settings):
        @model_validator(mode="after")
        def _tolerance_not_too_large(self):
            if self.marks.tolerance is not None and self.marks.tolerance > 100:
                raise ValueError("tolerance is too large")
            return self

    monkeypatch.setattr(settings_module, "Settings", Crossed)

    with pytest.raises(click.UsageError, match=r"^settings: tolerance is too large"):
        load_settings(None, {"mark_tolerance": 200})


def test_units_default_to_millimetres(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    assert load_settings(None, {}).units == "mm"


def test_units_come_from_the_file_and_the_option_beats_it(tmp_path):
    cfg = _write(tmp_path, 'units = "cm"\n')

    assert load_settings(cfg, {}).units == "cm"
    assert load_settings(cfg, {"units": "in"}).units == "in"
    assert load_settings(cfg, {"units": None}).units == "cm"


@pytest.mark.parametrize(
    ("units", "layer_height", "kerf"),
    [("mm", 3.0, 0.3), ("cm", 0.3, 0.03), ("in", 3 / 25.4, 0.3 / 25.4)],
)
def test_the_default_sheet_and_kerf_are_millimetres_stated_in_the_units(
    tmp_path, monkeypatch, units, layer_height, kerf
):
    """TR-13: a mm default must not be read as inches (#62)."""
    monkeypatch.chdir(tmp_path)

    s = load_settings(None, {"units": units})

    assert s.layer_height == pytest.approx(layer_height)
    assert s.kerf == pytest.approx(kerf)


def test_the_units_of_the_file_convert_the_defaults_it_does_not_set(tmp_path):
    cfg = _write(tmp_path, 'units = "in"\n')

    s = load_settings(cfg, {})

    assert s.layer_height == pytest.approx(3 / 25.4)
    assert s.kerf == pytest.approx(0.3 / 25.4)


def test_the_units_option_converts_the_defaults_of_a_file_in_millimetres(tmp_path):
    """The file's own defaults are not carried over as inches (a dump and validate again)."""
    cfg = _write(tmp_path, '[marks]\nshapes = ["circle"]\n')

    s = load_settings(cfg, {"units": "in"})

    assert s.layer_height == pytest.approx(3 / 25.4)


def test_a_sheet_and_kerf_that_are_given_are_not_converted(tmp_path):
    """A value from the file or the command line is already in the units."""
    cfg = _write(tmp_path, 'units = "in"\nlayer_height = 0.125\nkerf = 0.01\n')

    assert (load_settings(cfg, {}).layer_height, load_settings(cfg, {}).kerf) == (0.125, 0.01)
    s = load_settings(None, {"units": "in", "layer_height": 2.0, "kerf": 0.5})
    assert (s.layer_height, s.kerf) == (2.0, 0.5)
    only_file = _write(tmp_path, "layer_height = 2\n", name="mm.toml")
    assert load_settings(only_file, {"units": "in"}).layer_height == 2.0


def test_the_kerf_option_beats_the_file(tmp_path):
    cfg = _write(tmp_path, "kerf = 0.2\n")

    assert load_settings(cfg, {}).kerf == 0.2
    assert load_settings(cfg, {"kerf": 0.4}).kerf == 0.4


@pytest.mark.parametrize(
    ("value", "reason"), [(-1.0, "must be >= 0"), (float("nan"), "must be a finite number")]
)
def test_a_bad_kerf_option_names_the_option(value, reason):
    with pytest.raises(click.BadParameter) as excinfo:
        load_settings(None, {"kerf": value})

    assert excinfo.value.param_hint == "--kerf"
    assert reason in excinfo.value.message


@pytest.mark.parametrize("colour", ["red", "#f00", "#ff0000", "rgb(255,0,0)", "rgb(255, 0, 0)"])
def test_a_colour_that_svg_reads_is_accepted(tmp_path, colour):
    cfg = _write(tmp_path, f'[output]\ncut_color = "{colour}"\nengrave_color = "{colour}"\n')

    s = load_settings(cfg, {})

    assert (s.output.cut_color, s.output.engrave_color) == (colour, colour)


def test_a_colour_is_stored_without_the_spaces_around_it():
    s = load_settings(None, {"cut_color": "  red ", "engrave_color": "#00f "})

    assert (s.output.cut_color, s.output.engrave_color) == ("red", "#00f")


def test_the_colour_options_beat_the_file(tmp_path):
    cfg = _write(tmp_path, '[output]\ncut_color = "blue"\nengrave_color = "green"\n')

    assert load_settings(cfg, {}).output.cut_color == "blue"
    s = load_settings(cfg, {"cut_color": "#f00", "engrave_color": None})
    assert (s.output.cut_color, s.output.engrave_color) == ("#f00", "green")


@pytest.mark.parametrize(
    ("option", "hint"),
    [("cut_color", "--cut-color"), ("engrave_color", "--engrave-color")],
)
@pytest.mark.parametrize("bad", ["notacolor", "", "none", "currentColor", "Red", "rgb(1,2)"])
def test_a_bad_colour_option_names_the_option(option, hint, bad):
    with pytest.raises(click.BadParameter) as excinfo:
        load_settings(None, {option: bad})

    assert excinfo.value.param_hint == hint
    assert f"{bad!r} is not a colour" in excinfo.value.message


@pytest.mark.parametrize(("units", "width"), [("mm", 0.01), ("cm", 0.001), ("in", 0.01 / 25.4)])
def test_the_hairline_default_is_millimetres_stated_in_the_units(units, width):
    assert load_settings(None, {"units": units}).output.hairline_width == pytest.approx(width)


def test_a_hairline_that_is_given_is_not_converted(tmp_path):
    cfg = _write(tmp_path, 'units = "in"\n[output]\nhairline_width = 0.0005\n')

    assert load_settings(cfg, {}).output.hairline_width == 0.0005


def test_a_file_that_sets_another_output_key_still_converts_the_hairline(tmp_path):
    """Only the key that was set is left alone, not the whole [output] table."""
    cfg = _write(tmp_path, 'units = "in"\n[output]\ncut_color = "blue"\n')

    s = load_settings(cfg, {})

    assert s.output.cut_color == "blue"
    assert s.output.hairline_width == pytest.approx(0.01 / 25.4)
