from abc import ABC, abstractmethod

from svgwrite import Drawing

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
    def draw(self, dwg: Drawing, shape: BaseShape) -> None:
        """Draws a shape on the given Drawing object.

        Parameters
        ----------
        dwg : Drawing
            The Drawing object to draw the shape on.
        shape : BaseShape
            The shape to draw.

        Returns
        -------
        None
        """
        pass
