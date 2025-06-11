from abc import ABC, abstractmethod

from svgwrite import Drawing

from src.layerforge.domain.shapes.base_shape import BaseShape


class ShapeDrawingStrategy(ABC):
    """Base class for drawing strategies for different shapes."""

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
