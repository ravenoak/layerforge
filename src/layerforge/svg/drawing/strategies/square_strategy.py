from svgwrite import Drawing

from layerforge.domain.shapes.base_shape import BaseShape

from .base_strategy import ShapeDrawingStrategy


class SquareDrawingStrategy(ShapeDrawingStrategy):
    """Drawing strategy for Square shapes."""

    def draw(self, dwg: Drawing, shape: BaseShape) -> None:
        """Draw the outline of a :class:`Square` on ``dwg``."""
        color = shape.color or "blue"
        points = self.outline_points(shape)
        dwg.add(dwg.polygon(points, stroke=color, fill="none"))
