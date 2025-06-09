from typing import List

from shapely.geometry import Point, Polygon

from .reference_mark import ReferenceMark


class ReferenceMarkAdjuster:
    """Adjust reference marks so they don't conflict with slice contours."""

    @staticmethod
    def adjust_marks(
        marks: List[ReferenceMark],
        contours: List[Polygon],
        min_distance: float = 10.0,
    ) -> List[ReferenceMark]:
        """Return a filtered list of ``marks`` respecting ``min_distance``."""
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
