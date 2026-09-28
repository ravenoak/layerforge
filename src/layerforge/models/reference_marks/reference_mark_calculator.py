from __future__ import annotations

import random
from collections.abc import Sequence

from shapely import make_valid
from shapely.geometry import Point, Polygon

from layerforge.utils import calculate_distance, polygon_parts

from .footprint import mark_reach
from .reference_mark import ReferenceMark
from .shape_choice import choose_shape

_SAMPLE_SEED = 0


def _fits_region(
    pt: Point,
    region: Polygon,
    boundary_polys: Sequence[Polygon],
    radius: float,
    min_web: float,
    min_distance: float,
) -> bool:
    """True when ``pt`` is in ``region`` and clear of every polygon's edge by enough margin.

    ``region`` is already eroded by ``min_distance`` from both pieces' own outlines (the pair's
    shrunk overlap, see the pair-local-marks design spec's note on erosion of an intersection),
    so membership in ``region`` alone gives that clearance for a freshly sampled point. A
    ``candidate`` inherited from an earlier run carries no such guarantee about ``region`` (it may
    predate the current erosion, or a caller may pass an unenroded region), so each piece's edge
    is also checked against ``min_distance`` directly here; in the pre-eroded case that check is
    redundant with ``region.contains``, not wrong. The shape-dependent ``radius + min_web`` margin
    is checked against each piece individually either way.
    """
    margin = max(min_distance, radius + min_web)
    return region.contains(pt) and all(
        poly.boundary.distance(pt) >= margin for poly in boundary_polys
    )


def _clear_of_gap(
    x: float,
    y: float,
    others: Sequence[ReferenceMark],
    min_distance: float,
    radius: float,
    min_web: float,
) -> bool:
    """True when ``(x, y)`` is far enough from every mark in ``others``.

    One shared gap for the whole check, using this mark's own radius, the same approximation
    the old whole-slice search used. The adjuster checks the exact footprints afterwards.
    """
    gap = max(min_distance, 2 * radius + min_web)
    return all(calculate_distance(x, y, other.x, other.y) >= gap for other in others)


class ReferenceMarkCalculator:
    """Chooses the reference mark for one pair's shared region (TR-9).

    ``choose_mark_for_pair`` reuses the first carried candidate that still fits; failing that, it
    tries sample points in the order ``_sample_points`` returns them (the centroid first, then a
    fixed-seed random sequence) and returns the first one that fits. This is first-fit, not a
    maximized stability score, so a mark often does land at or near the centroid, since that is
    usually the first point tried.
    """

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
            parts = polygon_parts(repaired)
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
            if poly.contains(candidate):
                cand_tuple = (candidate.x, candidate.y)
                if cand_tuple not in pts:
                    pts.append(cand_tuple)
        return pts

    @staticmethod
    def choose_mark_for_pair(
        region: Polygon,
        boundary_polys: Sequence[Polygon],
        candidates: Sequence[ReferenceMark],
        avoid: Sequence[ReferenceMark],
        *,
        min_distance: float,
        min_web: float,
        tolerance: float,
        available_shapes: Sequence[str],
        size: float,
        angle: float,
    ) -> ReferenceMark | None:
        """Return the mark for one pair's shared region (TR-9).

        Tries each of ``candidates`` first (TR-10: reuse before creating); a candidate that no
        longer fits ``region`` or now collides with ``avoid`` is retired — simply not returned,
        never mutated. ``avoid`` holds marks already committed on the same piece by a different
        pairing (a split or a merge) and is spacing-only, never a source of inheritance. Falls
        back to choosing a shape (#198: before the point, so the disc matches it) and sampling
        a fresh point in ``region``, clear of both ``avoid`` and every retired candidate (TR-10:
        a fresh point must never coincide with a mark position already ruled out this call, or it
        could be mistaken for that mark). In the one real caller, ``plan_marks``, ``avoid`` already
        contains everything ``candidates`` does, so this is a no-op there; it only matters when the
        function is called in isolation, as this module's own tests do. Returns ``None`` when
        nothing fits.
        """
        for candidate in candidates:
            radius = mark_reach(candidate.shape, candidate.size)
            pt = Point(candidate.x, candidate.y)
            # Identity, not equality: `calculate_slice_contours` builds each slice's pieces with
            # `symmetric_difference` (see `Model.calculate_slice_contours`), so real slice pieces
            # never spatially overlap and a carried point can fit at most one sibling's region.
            # `candidate` is therefore the only entry `avoid` could legitimately hold that is the
            # very mark being tested here, so comparing by object identity (not just by not being
            # a coincidentally-equal point) correctly excludes only that one entry.
            others = [m for m in avoid if m is not candidate]
            if _fits_region(
                pt, region, boundary_polys, radius, min_web, min_distance
            ) and _clear_of_gap(candidate.x, candidate.y, others, min_distance, radius, min_web):
                return candidate

        avoid_all = [*avoid, *candidates]
        shape = choose_shape(available_shapes)
        radius = mark_reach(shape, size)
        for x, y in ReferenceMarkCalculator._sample_points(region):
            pt = Point(x, y)
            if not _fits_region(pt, region, boundary_polys, radius, min_web, min_distance):
                continue
            if not _clear_of_gap(x, y, avoid_all, min_distance, radius, min_web):
                continue
            if any(calculate_distance(x, y, m.x, m.y) <= tolerance for m in avoid_all):
                continue
            return ReferenceMark(x=x, y=y, shape=shape, size=size, angle=angle)
        return None
