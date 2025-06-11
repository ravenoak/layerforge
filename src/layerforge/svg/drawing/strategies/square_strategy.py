from svgwrite import Drawing

from src.layerforge.domain.shapes import Square
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
        # TODO: Get stroke and fill from the shape or config
        # TODO: Add some of this as attributes to the Square class
        dwg.add(dwg.rect(insert=(square.x - square.size / 2, square.y - square.size / 2),
                         size=(square.size, square.size), stroke='blue', fill='none'))
