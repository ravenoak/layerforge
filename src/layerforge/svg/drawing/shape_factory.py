"""Factory utilities for creating shape instances."""

from layerforge.domain.shapes import Arrow, Circle, Square, Triangle
from layerforge.domain.shapes.base_shape import BaseShape
from typing import Any, cast

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


class ShapeFactory:
    """Factory class for creating shapes."""
    @staticmethod
    def get_shape(
        shape_type: str, *args: object, **kwargs: object
    ) -> BaseShape:
        """Return an instance of the shape registered under ``shape_type``.

        Raises
        ------
        ValueError
            If ``shape_type`` has not been registered.
        """

        shape_cls = _SHAPE_REGISTRY.get(shape_type)
        if not shape_cls:
            available = ", ".join(sorted(_SHAPE_REGISTRY))
            raise ValueError(
                f"Unknown shape type: {shape_type}. Available shapes: {available}"
            )
        return cast(BaseShape, cast(Any, shape_cls)(*args, **kwargs))
