from importlib import import_module
from typing import Any


def require_module(module: str, feature: str) -> Any:
    """Import ``module`` or raise an informative :class:`ImportError`."""
    try:
        return import_module(module)
    except ImportError as exc:
        pkg = module.split(".")[0]
        raise ImportError(
            f"{feature} requires the '{pkg}' package. Install it via 'pip install {pkg}'."
        ) from exc

