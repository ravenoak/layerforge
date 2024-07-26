from svgwrite import Drawing

from layerforge.domain.shapes import Circle
from .base_strategy import ShapeDrawingStrategy


class CircleDrawingStrategy(ShapeDrawingStrategy):
    """Drawing strategy for Circle shapes."""

    def draw(self, dwg: Drawing, circle: Circle) -> None:
        """Draws a Circle shape on the given Drawing object.

        Parameters
        ----------
        dwg : Drawing
            The Drawing object to draw the shape on.
        circle : Circle
            The Circle shape to draw.

        Returns
        -------
        None
        """
        # TODO: Get stroke and fill from the shape or config
        dwg.add(dwg.circle(center=(circle.x, circle.y), r=circle.radius, stroke='red', fill='none'))
