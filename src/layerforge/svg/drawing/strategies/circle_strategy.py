import math
from typing import cast

from svgwrite import Drawing
from svgwrite.base import BaseElement

from layerforge.domain.shapes import Circle
from layerforge.domain.shapes.base_shape import BaseShape

from .base_strategy import ShapeDrawingStrategy


class CircleDrawingStrategy(ShapeDrawingStrategy):
    """Drawing strategy for Circle shapes."""

    def element(self, dwg: Drawing, shape: BaseShape) -> BaseElement:
        """Return the element of a :class:`Circle`."""
        circle = cast(Circle, shape)
        element = dwg.circle(center=(circle.x, circle.y), r=circle.radius)
        # rotation has no visible effect for circles but is kept for consistency
        if circle.angle:
            element.rotate(math.degrees(circle.angle), center=(circle.x, circle.y))
        return element
