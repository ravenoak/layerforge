from __future__ import annotations

from typing import TYPE_CHECKING, List, Tuple

from shapely.geometry import Point, Polygon

from layerforge.utils import calculate_distance

if TYPE_CHECKING:
    from layerforge.models.slicing.slice import Slice


class ReferenceMarkCalculator:
    """Class to calculate reference marks for a slice.

    The calculator evaluates candidate points inside each polygon and selects
    those that maximize a simple geometric stability metric. The metric used is
    inspired by GDOP (Geometric Dilution of Precision) and rewards points that
    are well spread out.
    """

    @staticmethod
    def _stability_score(points: List[Tuple[float, float]]) -> float:
        """Return the total pairwise distance between ``points``."""
        score = 0.0
        for i, p1 in enumerate(points):
            for p2 in points[i + 1 :]:
                score += calculate_distance(p1[0], p1[1], p2[0], p2[1])
        return score

    @staticmethod
    def _sample_points(poly: Polygon, samples: int = 4) -> List[Tuple[float, float]]:
        """Return ``samples`` candidate points inside ``poly``."""
        pts = [(poly.centroid.x, poly.centroid.y)]
        minx, miny, maxx, maxy = poly.bounds
        # Generate additional random points within the polygon
        for _ in range(samples - 1):
            x = float(minx + (maxx - minx) * 0.25)
            y = float(miny + (maxy - miny) * 0.25)
            candidate = Point(x, y)
            if poly.contains(candidate):
                pts.append((candidate.x, candidate.y))
        return pts

    @staticmethod
    def get_stable_marks(
        layer: Slice,
        existing_marks: List[Tuple[float, float]],
        min_distance: float = 10.0,
    ) -> List[Tuple[float, float]]:
        """Return stable mark positions for ``layer``."""
        selected: List[Tuple[float, float]] = []
        for poly in layer.contours:
            # Try to inherit an existing mark that is inside the polygon
            inherited = None
            for x, y in existing_marks:
                pt = Point(x, y)
                if poly.contains(pt) and poly.boundary.distance(pt) >= min_distance:
                    if all(
                        calculate_distance(x, y, sx, sy) >= min_distance
                        for sx, sy in selected
                    ):
                        inherited = (x, y)
                        break
            if inherited:
                selected.append(inherited)
                continue

            candidates = ReferenceMarkCalculator._sample_points(poly)
            best_pt = None
            best_score = -1.0
            for cand in candidates:
                x, y = cand
                pt = Point(x, y)
                if poly.boundary.distance(pt) < min_distance:
                    continue
                if any(
                    calculate_distance(x, y, sx, sy) < min_distance
                    for sx, sy in selected
                ):
                    continue
                score = ReferenceMarkCalculator._stability_score(selected + [cand])
                if score > best_score:
                    best_score = score
                    best_pt = cand
            if best_pt:
                selected.append(best_pt)
        return selected
