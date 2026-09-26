"""Which pieces of adjacent layers overlap, and where (TR-2, TR-9)."""

import math
from collections.abc import Sequence
from dataclasses import dataclass

import shapely
from shapely.geometry import MultiPolygon, Polygon
from shapely.ops import unary_union


@dataclass(frozen=True)
class AdjacentPair:
    """A piece of one layer and a piece of the layer above that overlap.

    Attributes
    ----------
    lower : int
        The index of the piece in the lower layer.
    upper : int
        The index of the piece in the layer above.
    overlap : Polygon | MultiPolygon
        The part of the plane that both pieces cover. It can have holes, and it can have
        several parts.
    shrunk : Polygon | MultiPolygon
        ``overlap`` moved in by the clearance. It is empty when the clearance is too large.
    """

    lower: int
    upper: int
    overlap: Polygon | MultiPolygon
    shrunk: Polygon | MultiPolygon


def _check(name: str, value: float) -> None:
    if not math.isfinite(value) or value < 0:
        raise ValueError(f"{name} must be a finite number of 0 or more, got {value}")


def _area_of(geometry: shapely.Geometry) -> Polygon | MultiPolygon:
    """Return the polygonal part of ``geometry``: lines and points have no area to share."""
    parts = [part for part in shapely.get_parts(geometry) if isinstance(part, Polygon)]
    merged = unary_union(parts) if parts else Polygon()
    return merged if isinstance(merged, (Polygon, MultiPolygon)) else Polygon()


def adjacent_pairs(
    layers: Sequence[Sequence[Polygon]],
    *,
    min_overlap_area: float = 0.0,
    clearance: float = 0.0,
) -> list[list[AdjacentPair]]:
    """Return the pairs of overlapping pieces of each two adjacent layers.

    Entry ``i`` of the result holds the pairs of a piece of ``layers[i]`` and a piece of
    ``layers[i + 1]``, so the result is one shorter than ``layers``. A pair needs an overlap
    with an area above 0 and of at least ``min_overlap_area``. Pieces that only touch at an
    edge or a point are not a pair, and a piece inside another is.

    Parameters
    ----------
    layers : sequence of sequence of Polygon
        The pieces of each layer, from the lowest layer up.
    min_overlap_area : float
        The least overlap that counts, in squared units. Default 0: any overlap counts.
    clearance : float
        The distance to move each overlap in by to get ``AdjacentPair.shrunk``. Default 0.

    Raises
    ------
    ValueError
        If ``min_overlap_area`` or ``clearance`` is not a finite number of 0 or more.
    """
    _check("min_overlap_area", min_overlap_area)
    _check("clearance", clearance)

    result: list[list[AdjacentPair]] = []
    for lower_layer, upper_layer in zip(layers, layers[1:], strict=False):
        pairs: list[AdjacentPair] = []
        for i, lower in enumerate(lower_layer):
            for j, upper in enumerate(upper_layer):
                if not lower.intersects(upper):
                    continue
                overlap = _area_of(lower.intersection(upper))
                if overlap.area <= 0 or overlap.area < min_overlap_area:
                    continue
                shrunk = overlap.buffer(-clearance) if clearance else overlap
                pairs.append(AdjacentPair(i, j, overlap, shrunk))
        result.append(pairs)
    return result
