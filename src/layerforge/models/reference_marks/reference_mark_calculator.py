from __future__ import annotations

import random
from typing import TYPE_CHECKING

from shapely import make_valid
from shapely.geometry import Point, Polygon

from layerforge.utils import calculate_distance

from .config import ReferenceMarkConfig
from .footprint import mark_reach, mark_size_at

if TYPE_CHECKING:
    from layerforge.models.slicing.slice import Slice


_SAMPLE_SEED = 0


class ReferenceMarkCalculator:
    """Class to calculate reference marks for a slice.

    The calculator evaluates candidate points inside each polygon and selects
    those that maximize a simple geometric stability metric. The metric used is
    inspired by GDOP (Geometric Dilution of Precision) and rewards points that
    are well spread out.  Marks therefore rarely lie exactly at the centroid of
    the contour; rather, candidates are sampled and the most stable arrangement
    is chosen.
    """

    @staticmethod
    def _stability_score(points: list[tuple[float, float]]) -> float:
        """Return the total pairwise distance between ``points``."""
        score = 0.0
        for i, p1 in enumerate(points):
            for p2 in points[i + 1 :]:
                score += calculate_distance(p1[0], p1[1], p2[0], p2[1])
        return score

    @staticmethod
    def _sample_points(poly: Polygon, samples: int = 4) -> list[tuple[float, float]]:
        """Return ``samples`` candidate points inside ``poly``.

        The centroid is returned when it lies inside ``poly`` (it may not, for a
        polygon with a hole or a concave one). Additional points are randomly
        sampled within the bounding box until ``samples`` unique points that are
        contained within ``poly`` are found.  Sampling uses a fixed seed, so the
        same polygon always gives the same points.
        """
        rng = random.Random(_SAMPLE_SEED)
        if not poly.is_valid:
            # Keep the largest polygon of the repaired shape, holes included.
            repaired = make_valid(poly)
            parts = [g for g in getattr(repaired, "geoms", [repaired]) if isinstance(g, Polygon)]
            if parts:
                poly = max(parts, key=lambda g: g.area)

        centroid = poly.centroid
        pts = [(centroid.x, centroid.y)] if poly.contains(centroid) else []
        minx, miny, maxx, maxy = poly.bounds

        # Keep sampling until we have the desired number of unique points. Limit
        # the number of attempts to avoid an infinite loop for degenerate
        # polygons.
        attempts = 0
        max_attempts = samples * 10
        while len(pts) < samples and attempts < max_attempts:
            attempts += 1
            x = rng.uniform(minx, maxx)
            y = rng.uniform(miny, maxy)
            candidate = Point(x, y)
            try:
                inside = poly.contains(candidate)
            except Exception:
                inside = False
            if inside:
                cand_tuple = (candidate.x, candidate.y)
                if cand_tuple not in pts:
                    pts.append(cand_tuple)
        return pts

    @staticmethod
    def get_stable_marks(
        layer: Slice,
        existing_marks: list[tuple[float, float]],
        config: ReferenceMarkConfig | None = None,
    ) -> list[tuple[float, float]]:
        """Return stable mark positions for ``layer`` respecting ``config.min_distance``.

        The hole of a mark must fit too (TR-5). Its shape and angle are not known yet for a
        new mark, so a mark is taken as a disc that holds the outline of every available
        shape at any angle. Its radius is the farthest reach of those outlines from the
        centre, which is a little over half the size for the circle (#157). The disc must
        lie inside the piece with ``layer.min_web`` to spare, and two discs must be
        ``layer.min_web`` apart.
        """
        cfg = config or ReferenceMarkConfig()
        min_distance = cfg.min_distance
        min_web = layer.min_web
        reach_per_size = max(mark_reach(name, 1.0) for name in cfg.available_shapes)

        def radius(x: float, y: float) -> float:
            return mark_size_at(cfg, layer.origin, x, y) * reach_per_size

        def clear_of_outline(x: float, y: float, poly: Polygon) -> bool:
            edge = poly.boundary.distance(Point(x, y))
            return edge >= min_distance and edge >= radius(x, y) + min_web

        def clear_of(x: float, y: float, other: tuple[float, float]) -> bool:
            gap = radius(x, y) + radius(*other) + min_web
            return calculate_distance(x, y, other[0], other[1]) >= max(min_distance, gap)

        selected: list[tuple[float, float]] = []
        for poly in layer.contours:
            # Try to inherit an existing mark that is inside the polygon
            inherited = None
            for x, y in existing_marks:
                pt = Point(x, y)
                if (
                    poly.contains(pt)
                    and clear_of_outline(x, y, poly)
                    and all(clear_of(x, y, other) for other in selected)
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
                if not clear_of_outline(x, y, poly):
                    continue
                if not all(clear_of(x, y, other) for other in selected):
                    continue
                # A point within the snapping range of a stored mark, or of a mark
                # chosen in this slice, would be taken for that mark (TR-10). The
                # stored mark did not pass the checks above, so skip the point.
                if any(
                    calculate_distance(x, y, mx, my) <= cfg.tolerance
                    for mx, my in existing_marks + selected
                ):
                    continue
                score = ReferenceMarkCalculator._stability_score(selected + [cand])
                if score > best_score:
                    best_score = score
                    best_pt = cand
            if best_pt:
                selected.append(best_pt)
        return selected

    @staticmethod
    def get_potential_marks(
        layer: Slice,
        existing_marks: list[tuple[float, float]],
        config: ReferenceMarkConfig | None = None,
    ) -> list[tuple[float, float]]:
        """Compatibility alias for :meth:`get_stable_marks`."""
        return ReferenceMarkCalculator.get_stable_marks(layer, existing_marks, config=config)
