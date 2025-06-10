"""Factory utilities for creating shape instances."""

from layerforge.domain.shapes import Arrow, Circle, Square, Triangle

# Registry mapping shape names to their implementing classes
_SHAPE_REGISTRY: dict[str, type] = {
    "circle": Circle,
    "square": Square,
    "triangle": Triangle,
    "arrow": Arrow,
}


def register_shape(name: str, cls: type) -> None:
    """Register ``cls`` under ``name`` in the factory registry."""
    _SHAPE_REGISTRY[name] = cls


class ShapeFactory:
    """Factory class for creating shapes."""
    @staticmethod
    def get_shape(shape_type: str, *args, **kwargs) -> object:
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
        return shape_cls(*args, **kwargs)
