from svgwrite import Drawing

from layerforge.domain.shapes.base_shape import BaseShape

from .base_strategy import ShapeDrawingStrategy


class TriangleDrawingStrategy(ShapeDrawingStrategy):
    """Drawing strategy for Triangle shapes."""

    def draw(self, dwg: Drawing, shape: BaseShape) -> None:
        """Draw the outline of a :class:`Triangle` on ``dwg``."""
        color = shape.color or "green"
        points = self.outline_points(shape)
        dwg.add(dwg.polygon(points, stroke=color, fill="none"))
