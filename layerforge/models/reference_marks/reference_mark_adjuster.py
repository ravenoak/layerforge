from typing import List, Tuple

from shapely.geometry import Point, Polygon


class ReferenceMarkAdjuster:
    """Adjust the reference marks to avoid overlapping with the contours."""

    @staticmethod
    def adjust_marks(
        marks: List[Tuple[float, float, str, float]],
        contours: List[Polygon],
        min_distance: float = 10.0,
    ) -> List[Tuple[float, float, str, float]]:
        """Adjust the reference marks to avoid overlapping with the contours.

        Parameters
        ----------
        marks : List[Tuple[float, float, str, float]]
            A list of reference marks represented as tuples ``(x, y, shape, size)``.
        contours : List[Polygon]
            A list of polygons to avoid overlapping with.
        min_distance : float, optional
            The minimum distance between marks and contours.

        Returns
        -------
        List[Tuple[float, float, str, float]]
            The adjusted reference marks.
        """
        adjusted_marks = []
        for mark in marks:
            mark_point = Point(mark[0], mark[1])
            is_too_close = False
            for model_polygon in contours:
                if model_polygon.boundary.distance(mark_point) < min_distance:
                    is_too_close = True
                    break
            if not is_too_close:
                is_overlapping = False
                for adj_mark in adjusted_marks:
                    adj_mark_point = Point(adj_mark[0], adj_mark[1])
                    if mark_point.distance(adj_mark_point) < min_distance:
                        is_overlapping = True
                        break
                if not is_overlapping:
                    adjusted_marks.append(mark)
        return adjusted_marks
