from svgwrite import Drawing

from layerforge.domain.shapes.base_shape import BaseShape

from .base_strategy import ShapeDrawingStrategy


class ArrowDrawingStrategy(ShapeDrawingStrategy):
    """Drawing strategy for Arrow shapes."""

    def draw(self, dwg: Drawing, shape: BaseShape) -> None:
        """Draw the outline of a :class:`Arrow` on ``dwg``."""
        color = shape.color or "black"
        points = self.outline_points(shape)
        dwg.add(dwg.polygon(points, stroke=color, fill="none"))
