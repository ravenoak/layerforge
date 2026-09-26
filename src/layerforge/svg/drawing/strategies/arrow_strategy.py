from svgwrite import Drawing
from svgwrite.base import BaseElement

from layerforge.domain.shapes.base_shape import BaseShape

from .base_strategy import ShapeDrawingStrategy


class ArrowDrawingStrategy(ShapeDrawingStrategy):
    """Drawing strategy for Arrow shapes."""

    def element(self, dwg: Drawing, shape: BaseShape) -> BaseElement:
        """Return the outline of an :class:`Arrow`."""
        return dwg.polygon(self.outline_points(shape))
