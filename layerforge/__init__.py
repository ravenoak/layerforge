from __future__ import annotations

from pathlib import Path
from importlib.metadata import PackageNotFoundError, version as _pkg_version
import tomllib


_DEFAULT_VERSION = "0.0.0"


def _load_version() -> str:
    """Return the package version defined in ``pyproject.toml``.

    Falls back to the installed distribution metadata if ``pyproject.toml`` is
    not present (e.g. in an installed package).
    """
    pyproject = Path(__file__).resolve().parent.parent / "pyproject.toml"
    if pyproject.exists():
        try:
            with pyproject.open("rb") as f:
                data = tomllib.load(f)
            return str(data["tool"]["poetry"]["version"])
        except Exception:
            pass
    try:
        return _pkg_version("layerforge")
    except PackageNotFoundError:
        return _DEFAULT_VERSION


__version__ = _load_version()
__all__ = ["__version__"]


def get_version() -> str:
    """Return the current package version."""
    return __version__
