from .geometry import calculate_distance
from .optional_dependencies import require_module
from .shape_strategies import register_shape_strategies

__all__ = [
    "calculate_distance",
    "register_shape_strategies",
    "require_module",
]
