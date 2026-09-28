from .geometry import calculate_distance, polygon_parts
from .optional_dependencies import require_module
from .shape_strategies import register_shape_strategies

__all__ = [
    "calculate_distance",
    "polygon_parts",
    "register_shape_strategies",
    "require_module",
]
