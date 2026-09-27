"""Marks chosen per pair of adjacent layers, retired when they no longer fit (#63, TR-9)."""

from __future__ import annotations

import shapely
from shapely.geometry import MultiPolygon, Polygon

from layerforge.models.slicing.adjacency import adjacent_pairs

from .config import ReferenceMarkConfig, require
from .reference_mark import ReferenceMark
from .reference_mark_calculator import ReferenceMarkCalculator


def _largest_part(region: Polygon | MultiPolygon) -> Polygon | None:
    """Return the biggest polygon of ``region``, or ``None`` if it has no area.

    A pair's shrunk overlap can be split into several disjoint pieces; phase 1 places a mark
    in the largest one only (a documented simplification, see the design spec's Non-goals).
    """
    parts = [p for p in shapely.get_parts(region) if isinstance(p, Polygon) and p.area > 0]
    return max(parts, key=lambda p: p.area) if parts else None


def plan_marks(
    contours: list[list[Polygon]], config: ReferenceMarkConfig, layer_height: float
) -> list[list[ReferenceMark]]:
    """Return the marks for every slice of ``contours``, chosen per pair of adjacent layers.

    ``contours[i]`` is the pieces of slice ``i``. The result is the same length, one list of
    marks per slice. A mark is chosen inside the shrunk overlap of two adjacent pieces (TR-9)
    and is retired -- excluded from the next pair's candidates -- the moment it no longer fits.
    Retirement only ever looks at the immediately previous pair; nothing looks further back.
    """
    cfg = config.resolved(layer_height)
    min_distance = require(cfg.min_distance, "min_distance")
    tolerance = require(cfg.tolerance, "tolerance")
    size = require(cfg.size, "size")
    min_web = cfg.min_web_ratio * layer_height
    pairs = adjacent_pairs(contours, min_overlap_area=cfg.min_overlap_area, clearance=min_distance)

    result: list[list[ReferenceMark]] = [[] for _ in contours]
    carried: dict[int, list[ReferenceMark]] = {}
    on_slice: dict[int, list[ReferenceMark]] = {}
    for i, boundary in enumerate(pairs):
        next_carried: dict[int, list[ReferenceMark]] = {}
        next_on_slice: dict[int, list[ReferenceMark]] = {}
        for pair in boundary:
            region = _largest_part(pair.shrunk)
            if region is None:
                continue
            lower_poly = contours[i][pair.lower]
            upper_poly = contours[i + 1][pair.upper]
            avoid = [*on_slice.get(pair.lower, []), *next_on_slice.get(pair.upper, [])]
            mark = ReferenceMarkCalculator.choose_mark_for_pair(
                region,
                [lower_poly, upper_poly],
                carried.get(pair.lower, []),
                avoid,
                min_distance=min_distance,
                min_web=min_web,
                tolerance=tolerance,
                available_shapes=cfg.available_shapes,
                size=size,
                angle=cfg.angle,
            )
            if mark is None:
                continue
            result[i].append(mark)
            result[i + 1].append(mark)
            on_slice.setdefault(pair.lower, []).append(mark)
            next_carried.setdefault(pair.upper, []).append(mark)
            next_on_slice.setdefault(pair.upper, []).append(mark)
        carried, on_slice = next_carried, next_on_slice
    return result
