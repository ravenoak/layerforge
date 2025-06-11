from abc import ABC, abstractmethod

from typing import TYPE_CHECKING

from layerforge.utils.optional_dependencies import require_module

if TYPE_CHECKING:  # pragma: no cover - import only for type checking
    from svgwrite import Drawing
else:  # pragma: no cover - imported lazily for runtime
    Drawing = require_module("svgwrite", "ShapeDrawingStrategy").Drawing  # type: ignore

from layerforge.domain.shapes.base_shape import BaseShape


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
