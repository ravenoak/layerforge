import math
from typing import TYPE_CHECKING, TypeAlias

from layerforge.utils.optional_dependencies import require_module

if TYPE_CHECKING:
    from svgwrite import Drawing as SvgDrawing
    Drawing: TypeAlias = SvgDrawing
else:
    Drawing: TypeAlias = require_module("svgwrite", "SquareDrawingStrategy").Drawing  # type: ignore

from layerforge.domain.shapes import Square
from layerforge.domain.shapes.base_shape import BaseShape
from .base_strategy import ShapeDrawingStrategy
from typing import cast


class SquareDrawingStrategy(ShapeDrawingStrategy):
    """Drawing strategy for Square shapes."""

    def draw(self, dwg: Drawing, shape: BaseShape) -> None:
        """Draw a :class:`Square` shape on ``dwg``."""
        square = cast(Square, shape)
        color = square.color or 'blue'
        element = dwg.rect(
            insert=(square.x - square.size / 2, square.y - square.size / 2),
            size=(square.size, square.size),
            stroke=color,
            fill='none',
        )
        if square.angle:
            element.rotate(math.degrees(square.angle), center=(square.x, square.y))
        dwg.add(element)
