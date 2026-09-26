import math
from dataclasses import dataclass
from typing import ClassVar

from shapely.geometry import Point, Polygon

from .base_shape import BaseShape

_SEGMENTS_PER_QUARTER = 16


@dataclass
class Circle(BaseShape):
    """A circle shape for reference marks."""

    symmetry_order: ClassVar[int | None] = None

    def type(self) -> str:
        """Return the type of the shape. Always 'circle' for this class.

        Returns
        -------
        str
            The type of the shape. Always 'circle'.
        """
        return "circle"

    @property
    def radius(self) -> float:
        """Return the radius of the circle.

        Returns
        -------
        float
            The radius of the circle.
        """
        return self.size / 2

    def outline(self) -> Polygon:
        """Return a polygon that holds the circle, for checks.

        The vertices lie on a circle a little larger than the mark (by 0.12%), so the edges
        stay outside the true circle and a check never passes a circle that crosses an edge.
        The drawing is an exact circle.
        """
        edge_gap = math.cos(math.pi / (4 * _SEGMENTS_PER_QUARTER))
        return Point(self.x, self.y).buffer(self.radius / edge_gap, quad_segs=_SEGMENTS_PER_QUARTER)
