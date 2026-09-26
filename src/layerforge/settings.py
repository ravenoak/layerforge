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

from layerforge.domain.shapes.registry import registered_shapes
from layerforge.models.reference_marks import ReferenceMarkConfig

DEFAULT_FILE = Path("layerforge.toml")

_DEFAULTS = ReferenceMarkConfig()
_STRICT = ConfigDict(extra="forbid", strict=True, allow_inf_nan=False)

# Command line option name -> key path in the file. Options not listed here
# (--mark-color, --scale-factor, --target-height, --stl-file, --output-folder)
# are not settings.
_OPTION_KEYS: dict[str, tuple[str, ...]] = {
    "units": ("units",),
    "layer_height": ("layer_height",),
    "mark_size": ("marks", "size"),
    "mark_tolerance": ("marks", "tolerance"),
    "mark_min_distance": ("marks", "min_distance"),
    "available_shapes": ("marks", "shapes"),
    "mark_angle": ("marks", "angle"),
}
_OPTION_HINTS = {keys: "--" + name.replace("_", "-") for name, keys in _OPTION_KEYS.items()}


class MarkSettings(BaseModel):
    """The ``[marks]`` table."""

    model_config = _STRICT

    size: float | None = Field(default=None, gt=0)
    tolerance: float = Field(default=_DEFAULTS.tolerance, ge=0)
    min_distance: float = Field(default=_DEFAULTS.min_distance, ge=0)
    shapes: list[str] = Field(default_factory=lambda: list(_DEFAULTS.available_shapes))
    angle: float = math.degrees(_DEFAULTS.angle)  # degrees, as the option takes them
    min_web_ratio: float = Field(default=_DEFAULTS.min_web_ratio, ge=0)  # no option (TR-16)

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


class Settings(BaseModel):
    """Every setting of a run."""

    model_config = _STRICT

    units: Literal["mm", "cm", "in"] = "mm"
    layer_height: float = Field(default=3.0, gt=0)
    marks: MarkSettings = Field(default_factory=MarkSettings)


def load_settings(path: Path | None, overrides: Mapping[str, object]) -> Settings:
    """Merge the defaults, the config file and the command line values.

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
    merged = file_settings.model_dump()
    for option, value in overrides.items():
        if value is None:
            continue
        *parents, leaf = _OPTION_KEYS[option]
        table = merged
        for name in parents:
            table = table[name]
        table[leaf] = value
    try:
        return Settings.model_validate(merged)
    except ValidationError as exc:
        # The file values passed above, so the bad value came from an option or from
        # a check across keys. A key that has no option is named by its key.
        error = exc.errors()[0]
        hint = _OPTION_HINTS.get(tuple(str(part) for part in error["loc"]))
        if hint is None:
            raise click.UsageError(f"{_key(error) or 'settings'}: {_message(error)}") from exc
        raise click.BadParameter(_message(error), param_hint=hint) from exc


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
