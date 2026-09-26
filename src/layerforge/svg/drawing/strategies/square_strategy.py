from svgwrite import Drawing
from svgwrite.base import BaseElement

from layerforge.domain.shapes.base_shape import BaseShape

from .base_strategy import ShapeDrawingStrategy


class SquareDrawingStrategy(ShapeDrawingStrategy):
    """Drawing strategy for Square shapes."""

    def element(self, dwg: Drawing, shape: BaseShape) -> BaseElement:
        """Return the outline of a :class:`Square`."""
        return dwg.polygon(self.outline_points(shape))
