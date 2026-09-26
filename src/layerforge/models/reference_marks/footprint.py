"""The hole a mark makes, and how far it reaches."""

import math

from shapely.geometry import Polygon

from layerforge.domain.shapes.registry import ShapeFactory

from .reference_mark import ReferenceMark


def mark_footprint(mark: ReferenceMark) -> Polygon:
    """Return the outline of the hole that ``mark`` makes (TR-5, TR-7)."""
    shape = ShapeFactory.get_shape(mark.shape, mark.x, mark.y, mark.size, angle=mark.angle)
    return shape.outline()


def mark_reach(shape: str, size: float) -> float:
    """Return how far the outline of a ``shape`` of ``size`` reaches from its centre.

    Measured on the outline the adjuster checks. It is ``size / 2`` for the square, the
    triangle and the arrow, and a little more for the circle, whose outline is a polygon
    just outside the drawn circle (#157).
    """
    outline = ShapeFactory.get_shape(shape, 0.0, 0.0, size).outline()
    return max(math.hypot(x, y) for x, y in outline.exterior.coords)
