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
        match = re.fullmatch(r"\| `([\w.]+)` \| `(--[\w-]+)` \| (.+) \|", line)
        if match:
            key, option, default = match.groups()
            rows[tuple(key.split("."))] = (option, default)
    return rows


def _cell_value(cell: str) -> object:
    """Read a Default cell: a TOML value in backticks, or `none` followed by an explanation."""
    if cell.startswith("none"):
        return None
    text = cell.strip("`")
    return tomllib.loads(f"v = {text}")["v"] if text not in {"mm", "cm", "in"} else text


def test_the_keys_table_lists_every_setting_and_no_other():
    assert set(_table_rows()) == set(_leaves(Settings()))


@pytest.mark.parametrize(
    "key", sorted(_leaves(Settings())), ids=[".".join(k) for k in sorted(_leaves(Settings()))]
)
def test_the_keys_table_states_the_default_of_each_setting(key):
    _, cell = _table_rows()[key]
    assert _cell_value(cell) == _leaves(Settings())[key]


@pytest.mark.parametrize(
    "key", sorted(_OPTION_HINTS), ids=[".".join(k) for k in sorted(_OPTION_HINTS)]
)
def test_the_keys_table_names_the_option_of_each_setting(key):
    option, _ = _table_rows()[key]
    assert option == _OPTION_HINTS[key]


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
        ("default_tolerance", ("marks", "tolerance")),
        ("default_min_distance", ("marks", "min_distance")),
        ("default_shapes", ("marks", "shapes")),
    ],
)
def test_the_spec_config_block_states_the_default_of_each_setting(name, key):
    assert _spec_config()[name] == _leaves(Settings())[key]


def _help_text(option: str) -> str:
    """Return the help of ``option`` from ``--help``, with the line breaks joined."""
    text = " ".join(CliRunner().invoke(cli, ["--help"]).output.split())
    match = re.search(rf"{option} \S+ (.*?)(?= --[a-z]|$)", text)
    assert match, option
    return match[1]


@pytest.mark.parametrize(
    ("option", "key", "shown"),
    [
        ("--units", ("units",), lambda v: f"Default {v}"),
        ("--layer-height", ("layer_height",), lambda v: f"Default {v}"),
        ("--mark-tolerance", ("marks", "tolerance"), lambda v: f"Default {v}"),
        ("--mark-min-distance", ("marks", "min_distance"), lambda v: f"Default {v}"),
        ("--available-shapes", ("marks", "shapes"), lambda v: f"Default {','.join(v)}"),
        ("--mark-angle", ("marks", "angle"), lambda v: f"Default {v}"),
    ],
)
def test_the_help_text_states_the_default_of_each_option(option, key, shown):
    assert shown(_leaves(Settings())[key]) in _help_text(option)
