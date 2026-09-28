"""Marks chosen per pair of adjacent layers, retired when they no longer fit (#63, TR-9)."""

from __future__ import annotations

from shapely.geometry import MultiPolygon, Polygon

from layerforge.models.slicing.adjacency import adjacent_pairs
from layerforge.utils import polygon_parts

from .config import ReferenceMarkConfig, require
from .reference_mark import ReferenceMark
from .reference_mark_calculator import ReferenceMarkCalculator


def _largest_part(region: Polygon | MultiPolygon) -> Polygon | None:
    """Return the biggest polygon of ``region``, or ``None`` if it has no area.

    A pair's shrunk overlap can be split into several disjoint pieces; phase 1 places a mark
    in the largest one only (a documented simplification: see the design spec's "Design"
    section on erosion of an intersection; the choice of the largest part only, rather than
    every part, is not itself called out in the spec's Non-goals).
    """
    parts = polygon_parts(region)
    return max(parts, key=lambda p: p.area) if parts else None


def plan_marks(
    contours: list[list[Polygon]], config: ReferenceMarkConfig, layer_height: float
) -> list[list[ReferenceMark]]:
    """Return the marks for every slice of ``contours``, chosen per pair of adjacent layers.

    ``contours[i]`` is the pieces of slice ``i``. The result is the same length, one list of
    marks per slice. A mark is chosen inside the shrunk overlap of two adjacent pieces (TR-9)
    and is retired -- excluded from the next pair's candidates -- the moment it no longer fits.
    Reuse of a retired mark never survives past the one boundary where it stopped fitting.

    A boundary that places no mark at all -- because its region is empty or nothing sampled
    clears tolerance -- still owes the next boundary its spacing: the position(s) that were in
    play keep propagating, avoid-only, through consecutive no-mark boundaries until a piece
    either gets a mark of its own (which then takes over as what the boundary after it must
    avoid) or the run ends. This keeps a fresh mark from ever landing within tolerance of one
    that only just went missing (TR-10), without ever making the missing mark reusable.
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
            candidates = carried.get(pair.lower, [])
            avoid = [*on_slice.get(pair.lower, []), *next_on_slice.get(pair.upper, [])]
            region = _largest_part(pair.shrunk)
            if region is None:
                # `next_on_slice[pair.upper]` already holds every earlier pairing's contribution
                # into this same upper piece (that is the second half of `avoid`, above), and
                # `candidates` is always a subset of `on_slice.get(pair.lower, [])` (both are
                # populated together in the mark-found branch below). Extending by `avoid` and
                # `candidates` here would re-add both, doubling the list on every failed pairing
                # into a shared upper piece -- exponential on a merge. Only the new contribution,
                # `on_slice.get(pair.lower, [])`, needs to be added.
                next_on_slice.setdefault(pair.upper, []).extend(on_slice.get(pair.lower, []))
                continue
            lower_poly = contours[i][pair.lower]
            upper_poly = contours[i + 1][pair.upper]
            mark = ReferenceMarkCalculator.choose_mark_for_pair(
                region,
                [lower_poly, upper_poly],
                candidates,
                avoid,
                min_distance=min_distance,
                min_web=min_web,
                tolerance=tolerance,
                available_shapes=cfg.available_shapes,
                size=size,
                angle=cfg.angle,
            )
            if mark is None:
                # Same reasoning as the `region is None` branch above.
                next_on_slice.setdefault(pair.upper, []).extend(on_slice.get(pair.lower, []))
                continue
            # A reused candidate was already appended to `result[i]` -- either as a fresh mark
            # in an earlier boundary's `result[i + 1]`, or as this piece's own fresh mark just
            # below -- so only a freshly chosen mark (not one of `candidates`) needs adding here.
            if not any(mark is c for c in candidates):
                result[i].append(mark)
            result[i + 1].append(mark)
            on_slice.setdefault(pair.lower, []).append(mark)
            next_carried.setdefault(pair.upper, []).append(mark)
            next_on_slice.setdefault(pair.upper, []).append(mark)
        carried, on_slice = next_carried, next_on_slice
    return result
