"""Factory utilities for creating shape instances. They live in ``domain.shapes.registry``."""

from layerforge.domain.shapes.registry import ShapeFactory, register_shape, registered_shapes

__all__ = ["ShapeFactory", "register_shape", "registered_shapes"]
