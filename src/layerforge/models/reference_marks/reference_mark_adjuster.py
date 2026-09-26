from shapely.geometry import Point, Polygon

from .config import ReferenceMarkConfig
from .footprint import mark_footprint
from .reference_mark import ReferenceMark


class ReferenceMarkAdjuster:
    """Adjust reference marks so they don't conflict with slice contours."""

    @staticmethod
    def adjust_marks(
        marks: list[ReferenceMark],
        contours: list[Polygon],
        config: ReferenceMarkConfig | None = None,
        *,
        min_web: float = 0.0,
    ) -> list[ReferenceMark]:
        """Return a filtered list of ``marks`` that fit their piece (TR-5).

        A mark is dropped when its centre is closer than ``config.min_distance`` to an
        outline or to a mark already kept. It is also dropped when its whole hole does not
        lie inside a contour, when the material between the hole and an outline is thinner
        than ``min_web``, or when the hole overlaps or comes within ``min_web`` of a hole
        already kept. The earlier mark stays.
        """
        cfg = config or ReferenceMarkConfig()
        min_distance = cfg.min_distance
        adjusted_marks: list[ReferenceMark] = []
        kept_footprints: list[Polygon] = []
        for mark in marks:
            mark_point = Point(mark.x, mark.y)
            # First, so that an unregistered shape name is an error for every mark (#162).
            footprint = mark_footprint(mark)
            is_too_close = any(
                polygon.boundary.distance(mark_point) < min_distance for polygon in contours
            )
            if is_too_close:
                continue
            fits = any(
                polygon.contains_properly(footprint)
                and polygon.boundary.distance(footprint) >= min_web
                for polygon in contours
            )
            if not fits:
                continue
            is_overlapping = any(
                mark_point.distance(Point(adj_mark.x, adj_mark.y)) < min_distance
                for adj_mark in adjusted_marks
            ) or any(
                footprint.intersects(kept) or footprint.distance(kept) < min_web
                for kept in kept_footprints
            )
            if not is_overlapping:
                adjusted_marks.append(mark)
                kept_footprints.append(footprint)
        return adjusted_marks
