import math
from typing import cast

from svgwrite import Drawing

from layerforge.domain.shapes import Circle
from layerforge.domain.shapes.base_shape import BaseShape

from .base_strategy import ShapeDrawingStrategy


class CircleDrawingStrategy(ShapeDrawingStrategy):
    """Drawing strategy for Circle shapes."""

    def draw(self, dwg: Drawing, shape: BaseShape) -> None:
        """Draw a :class:`Circle` shape on ``dwg``."""
        circle = cast(Circle, shape)
        color = circle.color or "red"
        # rotation has no visible effect for circles but is kept for consistency
        element = dwg.circle(
            center=(circle.x, circle.y), r=circle.radius, stroke=color, fill="none"
        )
        if circle.angle:
            element.rotate(math.degrees(circle.angle), center=(circle.x, circle.y))
        dwg.add(element)
