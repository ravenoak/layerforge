from typing import List, Optional, TYPE_CHECKING, TypeAlias

from layerforge.utils.optional_dependencies import require_module

if TYPE_CHECKING:  # pragma: no cover
    from shapely.geometry import Point as ShpPoint, Polygon as ShpPolygon
    Point: TypeAlias = ShpPoint
    Polygon: TypeAlias = ShpPolygon
else:
    _shapely = require_module("shapely.geometry", "ReferenceMarkManager")
    Point: TypeAlias = _shapely.Point
    Polygon: TypeAlias = _shapely.Polygon

from .config import ReferenceMarkConfig

from layerforge.utils import calculate_distance
from .reference_mark import ReferenceMark


class ReferenceMarkManager:
    """Manage reference marks on a slice of a 3D model.

    Attributes
    ----------
    marks : List[ReferenceMark]
        Collected reference marks for the model.
    """

    def __init__(self, config: ReferenceMarkConfig | None = None) -> None:
        self.marks: List[ReferenceMark] = []
        self.config = config or ReferenceMarkConfig()

    def find_mark_by_position(self, x: float, y: float, tolerance: float | None = None) -> Optional[ReferenceMark]:
        """Return the mark at ``(x, y)`` if within ``tolerance`` distance."""
        if tolerance is None:
            tolerance = self.config.tolerance
        for mark in self.marks:
            distance = calculate_distance(mark.x, mark.y, x, y)
            if distance <= tolerance:
                return mark
        return None

    def add_or_update_mark(
        self, x: float, y: float, shape: str, size: float, *, angle: float = 0.0, color: str | None = None
    ) -> None:
        """Add a new mark or update an existing one."""
        mark = self.find_mark_by_position(x, y)
        if mark:
            mark.shape = shape
            mark.size = size
            mark.angle = angle
            mark.color = color
        else:
            self.marks.append(
                ReferenceMark(x=x, y=y, shape=shape, size=size, angle=angle, color=color)
            )

    def find_mark_in_polygon(self, polygon: Polygon, min_distance: float | None = None) -> Optional[ReferenceMark]:
        """Return a stored mark inside ``polygon`` respecting ``min_distance``."""
        if min_distance is None:
            min_distance = self.config.min_distance
        for mark in self.marks:
            pt = Point(mark.x, mark.y)
            if polygon.contains(pt) and polygon.boundary.distance(pt) >= min_distance:
                return mark
        return None
