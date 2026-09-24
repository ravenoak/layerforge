import math
from typing import TYPE_CHECKING, TypeAlias

from layerforge.utils.optional_dependencies import require_module

if TYPE_CHECKING:
    from svgwrite import Drawing as SvgDrawing
    Drawing: TypeAlias = SvgDrawing
else:
    Drawing: TypeAlias = require_module("svgwrite", "CircleDrawingStrategy").Drawing  # type: ignore

from layerforge.domain.shapes import Circle
from layerforge.domain.shapes.base_shape import BaseShape
from .base_strategy import ShapeDrawingStrategy
from typing import cast


class CircleDrawingStrategy(ShapeDrawingStrategy):
    """Drawing strategy for Circle shapes."""

    def draw(self, dwg: Drawing, shape: BaseShape) -> None:
        """Draw a :class:`Circle` shape on ``dwg``."""
        circle = cast(Circle, shape)
        color = circle.color or 'red'
        # rotation has no visible effect for circles but is kept for consistency
        element = dwg.circle(
            center=(circle.x, circle.y), r=circle.radius, stroke=color, fill='none'
        )
        if circle.angle:
            element.rotate(math.degrees(circle.angle), center=(circle.x, circle.y))
        dwg.add(element)
