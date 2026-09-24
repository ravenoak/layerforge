from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version as _pkg_version

_DEFAULT_VERSION = "0.0.0"


def _load_version() -> str:
    """Return the installed distribution version, or ``0.0.0`` if not installed."""
    try:
        return _pkg_version("layerforge")
    except PackageNotFoundError:
        return _DEFAULT_VERSION


__version__ = _load_version()
__all__ = ["__version__"]


def get_version() -> str:
    """Return the current package version."""
    return __version__
