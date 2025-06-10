import math
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
        color = triangle.color or 'green'
        verts = triangle.vertices
        if triangle.angle:
            verts = []
            cx, cy = triangle.x, triangle.y
            for x, y in triangle.vertices:
                dx, dy = x - cx, y - cy
                r = math.hypot(dx, dy)
                theta = math.atan2(dy, dx) + triangle.angle
                verts.append((cx + r * math.cos(theta), cy + r * math.sin(theta)))

        dwg.add(dwg.polygon(verts, stroke=color, fill='none'))
