from typing import List, TYPE_CHECKING, TypeAlias

from layerforge.utils.optional_dependencies import require_module

if TYPE_CHECKING:  # pragma: no cover
    from shapely.geometry import Point as ShpPoint, Polygon as ShpPolygon
    Point: TypeAlias = ShpPoint
    Polygon: TypeAlias = ShpPolygon
else:
    _shapely = require_module("shapely.geometry", "ReferenceMarkAdjuster")
    Point: TypeAlias = _shapely.Point
    Polygon: TypeAlias = _shapely.Polygon

from .reference_mark import ReferenceMark
from .config import ReferenceMarkConfig


class ReferenceMarkAdjuster:
    """Adjust reference marks so they don't conflict with slice contours."""

    @staticmethod
    def adjust_marks(
        marks: List[ReferenceMark],
        contours: List[Polygon],
        config: ReferenceMarkConfig | None = None,
    ) -> List[ReferenceMark]:
        """Return a filtered list of ``marks`` respecting ``config.min_distance``."""
        cfg = config or ReferenceMarkConfig()
        min_distance = cfg.min_distance
        adjusted_marks: List[ReferenceMark] = []
        for mark in marks:
            mark_point = Point(mark.x, mark.y)
            is_too_close = any(
                polygon.boundary.distance(mark_point) < min_distance
                for polygon in contours
            )
            if is_too_close:
                continue
            is_overlapping = any(
                mark_point.distance(Point(adj_mark.x, adj_mark.y)) < min_distance
                for adj_mark in adjusted_marks
            )
            if not is_overlapping:
                adjusted_marks.append(mark)
        return adjusted_marks
