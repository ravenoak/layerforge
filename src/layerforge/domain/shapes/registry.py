"""Registry and factory for shape classes, by name."""

from typing import Any, cast

from .arrow import Arrow
from .base_shape import BaseShape
from .circle import Circle
from .square import Square
from .triangle import Triangle

# Registry mapping shape names to their implementing classes
_SHAPE_REGISTRY: dict[str, type[BaseShape]] = {
    "circle": Circle,
    "square": Square,
    "triangle": Triangle,
    "arrow": Arrow,
}


def register_shape(name: str, cls: type[BaseShape]) -> None:
    """Register ``cls`` under ``name`` in the factory registry."""
    _SHAPE_REGISTRY[name] = cls


def registered_shapes() -> list[str]:
    """Return the names of all registered shapes, sorted."""
    return sorted(_SHAPE_REGISTRY)


def _shape_class(shape_type: str) -> type[BaseShape]:
    """Return the class registered under ``shape_type``, or raise ``ValueError``."""
    shape_cls = _SHAPE_REGISTRY.get(shape_type)
    if not shape_cls:
        available = ", ".join(registered_shapes())
        raise ValueError(f"Unknown shape type: {shape_type}. Available shapes: {available}")
    return shape_cls


def shape_symmetry_order(shape_type: str) -> int | None:
    """Return the rotational symmetry order of the shape registered under ``shape_type``.

    ``None`` means unlimited (a circle).

    Raises
    ------
    ValueError
        If ``shape_type`` has not been registered.
    """
    return _shape_class(shape_type).symmetry_order


class ShapeFactory:
    """Factory class for creating shapes."""

    @staticmethod
    def get_shape(shape_type: str, *args: object, **kwargs: object) -> BaseShape:
        """Return an instance of the shape registered under ``shape_type``.

        Raises
        ------
        ValueError
            If ``shape_type`` has not been registered.
        """

        shape_cls = _shape_class(shape_type)
        return cast(BaseShape, cast(Any, shape_cls)(*args, **kwargs))
