import math
from dataclasses import dataclass
from typing import ClassVar

from shapely.geometry import Polygon

from .base_shape import BaseShape


@dataclass
class Square(BaseShape):
    """A square shape for reference marks. At angle 0 its sides are parallel to the axes."""

    symmetry_order: ClassVar[int | None] = 4

    def type(self) -> str:
        """Return the type of shape. Always 'square' for this class.

        Returns
        -------
        str
            The type of shape. Always 'square'.
        """
        return "square"

    def outline(self) -> Polygon:
        """Return the square, with its four corners on the circle of diameter ``size``."""
        corner = math.sqrt(0.5)
        return self._place(
            [(corner, corner), (-corner, corner), (-corner, -corner), (corner, -corner)]
        )
