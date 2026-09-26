import math
from dataclasses import dataclass
from typing import ClassVar

from shapely.geometry import Polygon

from .base_shape import BaseShape

# The base corners lie 140 degrees either side of the apex, so the apex angle is 40 degrees.
_BASE_ANGLE = math.radians(140)


@dataclass
class Triangle(BaseShape):
    """An isosceles triangle shape for reference marks. At angle 0 its apex points along +x."""

    symmetry_order: ClassVar[int | None] = 1

    def type(self) -> str:
        """Return the type of shape. Always 'triangle' for this class.

        Returns
        -------
        str
            The type of shape. Always 'triangle'.
        """
        return "triangle"

    def outline(self) -> Polygon:
        """Return the triangle, with its three corners on the circle of diameter ``size``."""
        return self._place(
            [
                (1.0, 0.0),
                (math.cos(_BASE_ANGLE), math.sin(_BASE_ANGLE)),
                (math.cos(_BASE_ANGLE), -math.sin(_BASE_ANGLE)),
            ]
        )
