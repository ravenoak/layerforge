import math
from dataclasses import dataclass
from typing import ClassVar

from shapely.geometry import Polygon

from .base_shape import BaseShape

_HEAD_HALF_WIDTH = 0.6
_SHAFT_HALF_WIDTH = 0.25
# The tail corners lie on the unit circle, so the anchor is the centre of the smallest
# circle that holds the arrow.
_TAIL_X = -math.sqrt(1 - _SHAFT_HALF_WIDTH**2)


@dataclass
class Arrow(BaseShape):
    """A closed arrow shape for reference marks. At angle 0 the tip points along +x."""

    symmetry_order: ClassVar[int | None] = 1

    def type(self) -> str:
        """Return the type of the shape. Always 'arrow' for this class.

        Returns
        -------
        str
            The type of the shape. Always 'arrow'.
        """
        return "arrow"

    def outline(self) -> Polygon:
        """Return the arrow as a polygon of seven vertices: tip, head, shaft and tail."""
        return self._place(
            [
                (1.0, 0.0),
                (0.0, _HEAD_HALF_WIDTH),
                (0.0, _SHAFT_HALF_WIDTH),
                (_TAIL_X, _SHAFT_HALF_WIDTH),
                (_TAIL_X, -_SHAFT_HALF_WIDTH),
                (0.0, -_SHAFT_HALF_WIDTH),
                (0.0, -_HEAD_HALF_WIDTH),
            ]
        )
