from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import ClassVar

from shapely import affinity
from shapely.geometry import Polygon


@dataclass
class BaseShape(ABC):
    """A base class for reference mark shapes.

    Every shape is a closed outline (TR-7). ``size`` is the diameter of the
    smallest circle around the anchor ``(x, y)`` that holds the outline. Angle 0
    points along +x and angles turn counter-clockwise, in radians.

    Attributes
    ----------
    x : float
        The x-coordinate of the anchor, the centre of the shape.
    y : float
        The y-coordinate of the anchor, the centre of the shape.
    size : float
        The diameter of the smallest circle around the anchor that holds the
        outline.
    symmetry_order : int or None
        The number of turns of the outline that map it onto itself in one full
        turn. ``None`` means unlimited (a circle).
    """

    x: float
    y: float
    size: float
    angle: float = 0.0
    color: str | None = None

    symmetry_order: ClassVar[int | None] = 1

    @abstractmethod
    def type(self) -> str:
        """Return the type of the shape.

        Returns
        -------
        str
            The type of the shape.
        """
        pass

    @abstractmethod
    def outline(self) -> Polygon:
        """Return the closed outline of the shape, in the coordinates of the anchor.

        Returns
        -------
        Polygon
            The outline, turned by ``angle`` around the anchor.
        """
        pass

    def _place(self, unit_vertices: list[tuple[float, float]]) -> Polygon:
        """Scale ``unit_vertices`` (radius 1, angle 0), turn and move them to the anchor."""
        radius = self.size / 2
        polygon = Polygon([(px * radius, py * radius) for px, py in unit_vertices])
        polygon = affinity.rotate(polygon, self.angle, origin=(0, 0), use_radians=True)
        return affinity.translate(polygon, xoff=self.x, yoff=self.y)
