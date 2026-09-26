"""A default has one source, `Settings()`. Every copy that a test can read must agree with it.

The copies covered are the keys table of docs/configuration.md, the `config` block of
specs/layerforge.allium and the `--help` text. The prose of docs/requirements.md is not
covered, and neither is the TR-16 table of docs/alignment_requirements.md, which holds
target defaults that differ on purpose. See "Defaults" in docs/development.md.
"""

import json
import re
import tomllib
from pathlib import Path

import pytest
from click.testing import CliRunner

from layerforge.cli import cli
from layerforge.models.reference_marks.config import TOLERANCE_FACTOR
from layerforge.settings import _OPTION_HINTS, Settings

ROOT = Path(__file__).resolve().parent.parent
CONFIGURATION = ROOT / "docs" / "configuration.md"
SPEC = ROOT / "specs" / "layerforge.allium"


def _leaves(settings: Settings) -> dict[tuple[str, ...], object]:
    """Return every setting by its key path, for example ``("marks", "size")``."""
    leaves: dict[tuple[str, ...], object] = {}
    for name, value in settings.model_dump().items():
        if isinstance(value, dict):
            leaves.update({(name, sub): v for sub, v in value.items()})
        else:
            leaves[(name,)] = value
    return leaves


def _table_rows() -> dict[tuple[str, ...], tuple[str, str]]:
    """Return the keys table of docs/configuration.md as {key path: (option, default cell)}."""
    rows: dict[tuple[str, ...], tuple[str, str]] = {}
    for line in CONFIGURATION.read_text().splitlines():
        match = re.fullmatch(r"\| `([\w.]+)` \| (`--[\w-]+`|none) \| (.+) \|", line)
        if match:
            key, option, default = match.groups()
            rows[tuple(key.split("."))] = (option.strip("`"), default)
    return rows


def _cell_value(cell: str) -> object:
    """Read a Default cell: a TOML value in backticks, or `none` followed by an explanation."""
    if cell.startswith("none"):
        return None
    return tomllib.loads(f"v = {cell.strip('`')}")["v"]


def test_the_keys_table_lists_every_setting_and_no_other():
    assert set(_table_rows()) == set(_leaves(Settings()))


@pytest.mark.parametrize(
    "key", sorted(_leaves(Settings())), ids=[".".join(k) for k in sorted(_leaves(Settings()))]
)
def test_the_keys_table_states_the_default_of_each_setting(key):
    _, cell = _table_rows()[key]
    assert _cell_value(cell) == _leaves(Settings())[key]


@pytest.mark.parametrize(
    "key", sorted(_leaves(Settings())), ids=[".".join(k) for k in sorted(_leaves(Settings()))]
)
def test_the_keys_table_names_the_option_of_each_setting(key):
    option, _ = _table_rows()[key]
    assert option == _OPTION_HINTS.get(key, "none")  # a setting with no option says none


def _spec_config() -> dict[str, object]:
    """Return the `default_*` entries of the `config` block of the spec."""
    block = re.search(r"^config \{\n(.*?)^\}", SPEC.read_text(), re.S | re.M)
    assert block
    values: dict[str, object] = {}
    for name, value in re.findall(
        r"^\s+(default_\w+): [\w<>]+ = (.+?)\s*(?:--.*)?$", block[1], re.M
    ):
        values[name] = json.loads(value)
    return values


@pytest.mark.parametrize(
    ("name", "key"),
    [
        ("default_units", ("units",)),
        ("default_layer_height", ("layer_height",)),
        ("default_kerf", ("kerf",)),
        ("default_angle", ("marks", "angle")),  # degrees in both, as the option takes them
        ("default_min_web_ratio", ("marks", "min_web_ratio")),
        ("default_min_hole_ratio", ("marks", "min_hole_ratio")),
        ("default_min_hole_kerf_factor", ("marks", "min_hole_kerf_factor")),
        ("default_shapes", ("marks", "shapes")),
        ("default_cut_color", ("output", "cut_color")),
        ("default_engrave_color", ("output", "engrave_color")),
        ("default_hairline_width", ("output", "hairline_width")),  # millimetres in both
    ],
)
def test_the_spec_config_block_states_the_default_of_each_setting(name, key):
    assert _spec_config()[name] == _leaves(Settings())[key]


# Their default is a rule, not a number (TR-6, TR-10), so the spec block has no entry for them.
DERIVED = [("marks", "size"), ("marks", "tolerance"), ("marks", "min_distance")]


@pytest.mark.parametrize("key", DERIVED, ids=[".".join(k) for k in DERIVED])
def test_a_derived_setting_has_no_default_number_and_no_spec_entry(key):
    """#164: the choice not to compare them is written here, and it fails if it changes."""
    assert _leaves(Settings())[key] is None
    assert f"default_{key[-1]}" not in _spec_config()


def test_the_tolerance_factor_of_the_spec_is_the_one_in_the_code():
    block = re.search(r"^config \{\n(.*?)^\}", SPEC.read_text(), re.S | re.M)
    assert block
    match = re.search(r"^\s+tolerance_factor: Decimal = ([\d.]+)", block[1], re.M)
    assert match
    assert float(match[1]) == TOLERANCE_FACTOR


def test_every_default_of_the_spec_config_block_is_compared():
    """A new `default_*` entry in the spec needs a row in the test above."""
    assert set(_spec_config()) == {
        "default_units",
        "default_layer_height",
        "default_kerf",
        "default_angle",
        "default_min_web_ratio",
        "default_min_hole_ratio",
        "default_min_hole_kerf_factor",
        "default_shapes",
        "default_cut_color",
        "default_engrave_color",
        "default_hairline_width",
    }


def _help_text(option: str) -> str:
    """Return the help of ``option`` from ``--help``, with the line breaks joined."""
    text = " ".join(CliRunner().invoke(cli, ["--help"]).output.split())
    match = re.search(rf"{option} \S+ (.*?)(?= --[a-z]|$)", text)
    assert match, option
    return match[1]


@pytest.mark.parametrize(
    ("option", "key", "shown"),
    [
        ("--units", ("units",), lambda v: f"Default {v}."),
        ("--layer-height", ("layer_height",), lambda v: f"Default {v} mm"),
        ("--kerf", ("kerf",), lambda v: f"Default {v} mm"),
        ("--available-shapes", ("marks", "shapes"), lambda v: f"Default {','.join(v)}."),
        ("--mark-angle", ("marks", "angle"), lambda v: f"Default {v}."),
        ("--cut-color", ("output", "cut_color"), lambda v: f"Default {v}."),
        ("--engrave-color", ("output", "engrave_color"), lambda v: f"Default {v}."),
    ],
)
def test_the_help_text_states_the_default_of_each_option(option, key, shown):
    assert shown(_leaves(Settings())[key]) in _help_text(option)


def test_the_help_text_states_how_each_derived_default_is_worked_out():
    marks = Settings().marks
    size = f"{marks.min_hole_ratio:g} x the layer height and {marks.min_hole_kerf_factor:g} x"
    assert size in _help_text("--mark-size")
    assert f"Default {TOLERANCE_FACTOR:g} x the mark size" in _help_text("--mark-tolerance")
    assert "Default: the mark size" in _help_text("--mark-min-distance")
