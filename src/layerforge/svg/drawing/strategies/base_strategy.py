from abc import ABC, abstractmethod

from svgwrite import Drawing
from svgwrite.base import BaseElement

from layerforge.domain.shapes.base_shape import BaseShape


class ShapeDrawingStrategy(ABC):
    """Base class for drawing strategies for different shapes."""

    @staticmethod
    def outline_points(shape: BaseShape) -> list[tuple[float, float]]:
        """Return the vertices of the outline of ``shape``, without the repeated first one.

        SVG closes a polygon itself, and shapely repeats the first vertex to close a ring.
        """
        return [(x, y) for x, y in shape.outline().exterior.coords][:-1]

    @abstractmethod
    def element(self, dwg: Drawing, shape: BaseShape) -> BaseElement:
        """Return the element that draws ``shape``, without adding it to ``dwg``.

        The element holds no stroke, width, fill or class. :meth:`StrategyContext.draw` adds
        them, so every shape is styled the same way.

        Parameters
        ----------
        dwg : Drawing
            The Drawing object that makes the element.
        shape : BaseShape
            The shape to draw.

        Returns
        -------
        BaseElement
            The element, not yet in ``dwg``.
        """
