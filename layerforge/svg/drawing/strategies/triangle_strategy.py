from svgwrite import Drawing

from layerforge.domain.shapes import Triangle
from .base_strategy import ShapeDrawingStrategy


class TriangleDrawingStrategy(ShapeDrawingStrategy):
    """Drawing strategy for Triangle shapes."""

    def draw(self, dwg: Drawing, triangle: Triangle) -> None:
        """Draws a Triangle shape on the given Drawing object.

        Parameters
        ----------
        dwg : Drawing
            The Drawing object to draw the shape on.
        triangle : Triangle
            The Triangle shape to draw.

        Returns
        -------
        None
        """
        # TODO: Get stroke and fill from the shape or config
        dwg.add(dwg.polygon(triangle.vertices, stroke='green', fill='none'))
