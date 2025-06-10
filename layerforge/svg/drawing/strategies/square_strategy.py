import math
from svgwrite import Drawing

from layerforge.domain.shapes import Square
from .base_strategy import ShapeDrawingStrategy


class SquareDrawingStrategy(ShapeDrawingStrategy):
    """Drawing strategy for Square shapes."""

    def draw(self, dwg: Drawing, square: Square) -> None:
        """Draws a Square shape on the given Drawing object.

        Parameters
        ----------
        dwg : Drawing
            The Drawing object to draw the shape on.
        square : Square
            The Square shape to draw.

        Returns
        -------
        None
        """
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
