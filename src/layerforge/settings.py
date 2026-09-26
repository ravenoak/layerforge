"""Settings for one run: defaults, an optional TOML file and command line values.

A setting is taken from the command line first, then the file, then its default.
The key names follow TR-16 in ``docs/alignment_requirements.md``. Each later issue
adds its own keys, so an unknown key is an error.
"""

from __future__ import annotations

import math
import tomllib
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Literal

import click
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator
from pydantic_core import ErrorDetails
from svgwrite.data.typechecker import Tiny12TypeChecker  # pyright: ignore[reportMissingTypeStubs]

from layerforge.domain.shapes.registry import registered_shapes
from layerforge.models.reference_marks import ReferenceMarkConfig
from layerforge.svg.style import SVGStyle
from layerforge.units import from_mm

DEFAULT_FILE = Path("layerforge.toml")

_DEFAULTS = ReferenceMarkConfig()
_STYLE = SVGStyle()
_STRICT = ConfigDict(extra="forbid", strict=True, allow_inf_nan=False)

# The colours that svgwrite writes for SVG Tiny: a name, #rgb, #rrggbb, rgb(r,g,b) or rgb(r%,g%,b%).
# Its checker is the one that would refuse the value later, while the SVG is drawn (#145).
_COLOUR_CHECKER: Any = Tiny12TypeChecker()

# Lengths whose default is stated in millimetres and converted to the run's units (TR-13).
# ``output.hairline_width`` is converted too, see ``_in_units``.
_MM_DEFAULTS = ("layer_height", "kerf")

# Command line option name -> key path in the file. Options not listed here
# (--scale-factor, --target-height, --stl-file, --output-folder) are not settings.
_OPTION_KEYS: dict[str, tuple[str, ...]] = {
    "units": ("units",),
    "layer_height": ("layer_height",),
    "kerf": ("kerf",),
    "mark_size": ("marks", "size"),
    "mark_tolerance": ("marks", "tolerance"),
    "mark_min_distance": ("marks", "min_distance"),
    "available_shapes": ("marks", "shapes"),
    "mark_angle": ("marks", "angle"),
    "cut_color": ("output", "cut_color"),
    "engrave_color": ("output", "engrave_color"),
}
_OPTION_HINTS = {keys: "--" + name.replace("_", "-") for name, keys in _OPTION_KEYS.items()}


class MarkSettings(BaseModel):
    """The ``[marks]`` table."""

    model_config = _STRICT

    # No number for these three: they come from the sheet, unless set (TR-6, TR-10).
    size: float | None = Field(default=None, gt=0)
    tolerance: float | None = Field(default=None, ge=0)
    min_distance: float | None = Field(default=None, ge=0)
    shapes: list[str] = Field(default_factory=lambda: list(_DEFAULTS.available_shapes))
    angle: float = math.degrees(_DEFAULTS.angle)  # degrees, as the option takes them
    min_web_ratio: float = Field(default=_DEFAULTS.min_web_ratio, ge=0)  # no option (TR-16)
    min_hole_ratio: float = Field(default=_DEFAULTS.min_hole_ratio, gt=0)  # no option (TR-16)
    min_hole_kerf_factor: float = Field(default=_DEFAULTS.min_hole_kerf_factor, ge=0)  # no option

    @field_validator("shapes")
    @classmethod
    def _known_shapes(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("must name at least one shape")
        unknown = [s for s in v if s not in registered_shapes()]
        if unknown:
            raise ValueError(
                f"unknown shape {', '.join(unknown)}. Available shapes: "
                f"{', '.join(registered_shapes())}"
            )
        return v


class OutputSettings(BaseModel):
    """The ``[output]`` table: how the SVG is drawn for a laser (TR-14)."""

    model_config = _STRICT

    cut_color: str = _STYLE.cut_color
    engrave_color: str = _STYLE.engrave_color
    hairline_width: float = Field(default=_STYLE.hairline_width, gt=0)  # no option (TR-16)

    @field_validator("cut_color", "engrave_color")
    @classmethod
    def _a_colour(cls, v: str) -> str:
        colour = v.strip()
        if not _COLOUR_CHECKER.is_color(colour):
            raise ValueError(
                f"{v!r} is not a colour. Use a name such as red, a hex value such as #f00, "
                "or rgb(255,0,0)"
            )
        return colour


class Settings(BaseModel):
    """Every setting of a run.

    ``layer_height``, ``kerf`` and ``output.hairline_width`` default to millimetres here.
    :func:`merge_settings` states a default that was not set in the units of the run, so read
    them from its result.
    """

    model_config = _STRICT

    units: Literal["mm", "cm", "in"] = "mm"
    layer_height: float = Field(default=3.0, gt=0)
    kerf: float = Field(default=_DEFAULTS.kerf, ge=0)
    marks: MarkSettings = Field(default_factory=MarkSettings)
    output: OutputSettings = Field(default_factory=OutputSettings)


def load_settings(path: Path | None, overrides: Mapping[str, object]) -> Settings:
    """Merge the defaults, the config file and the command line values.

    This is the one-call form for Python callers and tests. The command does not use it: it
    reads the file once with :func:`read_config_file`, names it on stderr, and then calls
    :func:`merge_settings`.

    Parameters
    ----------
    path : Path, optional
        The config file. When ``None``, ``layerforge.toml`` in the current
        directory is used if it exists.
    overrides : Mapping[str, object]
        Command line values by option name, for example ``mark_tolerance``. A
        value of ``None`` means the option was not given.

    Raises
    ------
    click.UsageError
        If the file cannot be read or holds a bad key or value. The message names
        the file and the key.
    click.BadParameter
        If a command line value is bad. The parameter hint names the option.
        A bad merged value for a key that has no option raises ``click.UsageError``
        and names the key instead, or ``settings`` when the error has no key.
    """
    path = find_config_file(path)
    return merge_settings(read_config_file(path) if path is not None else Settings(), overrides)


def merge_settings(file_settings: Settings, overrides: Mapping[str, object]) -> Settings:
    """Lay the command line values over settings that are already read and checked.

    Parameters
    ----------
    file_settings : Settings
        The settings of the config file, or the defaults when there is no file.
    overrides : Mapping[str, object]
        Command line values by option name. ``None`` means the option was not given.

    Raises
    ------
    click.BadParameter
        If a command line value is bad. The parameter hint names the option.
        A bad merged value for a key that has no option raises ``click.UsageError``
        and names the key instead, or ``settings`` when the error has no key.
    """
    # Only what was set: a default is applied again below, in the units of the run.
    merged = file_settings.model_dump(exclude_unset=True)
    for option, value in overrides.items():
        if value is None:
            continue
        *parents, leaf = _OPTION_KEYS[option]
        table = merged
        for name in parents:
            table = table.setdefault(name, {})
        table[leaf] = value
    try:
        return _in_units(Settings.model_validate(merged))
    except ValidationError as exc:
        # The file values passed above, so the bad value came from an option or from
        # a check across keys. A key that has no option is named by its key.
        error = exc.errors()[0]
        hint = _OPTION_HINTS.get(tuple(str(part) for part in error["loc"]))
        if hint is None:
            raise click.UsageError(f"{_key(error) or 'settings'}: {_message(error)}") from exc
        raise click.BadParameter(_message(error), param_hint=hint) from exc


def _in_units(settings: Settings) -> Settings:
    """State the millimetre defaults that nobody set in the units of the run (TR-13).

    A key is left alone when it was set, whatever else its table holds: a file that sets only
    ``output.cut_color`` still gets the hairline in the units of the run.
    """
    updates: dict[str, Any] = {
        name: from_mm(settings.units, getattr(settings, name))
        for name in _MM_DEFAULTS
        if name not in settings.model_fields_set
    }
    if "hairline_width" not in settings.output.model_fields_set:
        width = from_mm(settings.units, settings.output.hairline_width)
        updates["output"] = settings.output.model_copy(update={"hairline_width": width})
    return settings.model_copy(update=updates) if updates else settings


def find_config_file(path: Path | None) -> Path | None:
    """Return the config file to use: ``path``, else ``layerforge.toml`` if it exists."""
    if path is None and DEFAULT_FILE.is_file():
        return DEFAULT_FILE
    return path


def read_config_file(path: Path) -> Settings:
    """Read and check a config file on its own, without any command line values.

    Raises
    ------
    click.UsageError
        If the file cannot be read or holds a bad key or value. The message names
        the file and the key.
    """
    try:
        return Settings.model_validate(_read(path))
    except ValidationError as exc:
        error = exc.errors()[0]
        raise click.UsageError(f"{path}: {_key(error)}: {_message(error)}") from exc


def _read(path: Path) -> dict[str, Any]:
    try:
        with path.open("rb") as handle:
            return tomllib.load(handle)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise click.UsageError(f"{path}: {exc}") from exc


def _key(error: ErrorDetails) -> str:
    return ".".join(str(part) for part in error["loc"])


def _message(error: ErrorDetails) -> str:
    ctx = error.get("ctx", {})
    match error["type"]:
        case "greater_than":
            return f"must be > {ctx['gt']:g}"
        case "greater_than_equal":
            return f"must be >= {ctx['ge']:g}"
        case "finite_number":
            return "must be a finite number"
        case "value_error":
            return str(ctx["error"])
        case _:
            return error["msg"]
