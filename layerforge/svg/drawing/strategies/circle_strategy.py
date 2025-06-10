import math
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
        color = circle.color or 'red'
        # rotation has no visible effect for circles but is kept for consistency
        element = dwg.circle(
            center=(circle.x, circle.y), r=circle.radius, stroke=color, fill='none'
        )
        if circle.angle:
            element.rotate(math.degrees(circle.angle), center=(circle.x, circle.y))
        dwg.add(element)
