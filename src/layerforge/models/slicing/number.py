"""Where the layer number of a piece goes (TR-11)."""

import math
from collections.abc import Sequence
from dataclasses import dataclass
from typing import cast

import shapely
from shapely.geometry import Polygon, box
from shapely.ops import polylabel, unary_union

from layerforge.models.reference_marks import ReferenceMark
from layerforge.models.reference_marks.footprint import mark_footprint


@dataclass(frozen=True)
class NumberPlacement:
    """The centre of the number, and whether its box fits clear of the cuts."""

    x: float
    y: float
    fits: bool


def number_box(x: float, y: float, *, digits: int, height: float, width_factor: float) -> Polygon:
    """Return the box that holds a number of ``digits`` characters centred on ``(x, y)``.

    The width is ``width_factor * height`` for each character. The box is as tall as the text
    is, and text is drawn with a font size equal to its height, so the box is conservative.
    """
    half_w = width_factor * height * digits / 2
    return box(x - half_w, y - height / 2, x + half_w, y + height / 2)


def place_number(
    contour: Polygon,
    marks: Sequence[ReferenceMark],
    *,
    digits: int,
    height: float,
    width_factor: float,
    clearance: float,
) -> NumberPlacement:
    """Place the number of a piece where its box is farthest from every cut.

    The box must lie in ``contour``, ``clearance`` from its outline and holes, and
    ``clearance`` from the footprint of every mark. The valid centres are the material left
    after each cut is grown by the box, so an empty set proves that the number cannot fit. The
    centre is the point of the valid set that is farthest from its edge. When nothing fits,
    the centre is the point of the piece that is farthest from its edge, and ``fits`` is False.

    Raises
    ------
    ValueError
        If ``height`` or ``width_factor`` is not a finite number above 0, ``clearance`` is not
        a finite number of 0 or more, or ``digits`` is below 1.
    """
    for name, value in (("height", height), ("width_factor", width_factor)):
        if not math.isfinite(value) or value <= 0:
            raise ValueError(f"{name} must be a finite number above 0, got {value}")
    if not math.isfinite(clearance) or clearance < 0:
        raise ValueError(f"clearance must be a finite number of 0 or more, got {clearance}")
    if digits < 1:
        raise ValueError(f"digits must be at least 1, got {digits}")

    tolerance = height / 100
    allowed = contour.buffer(-clearance) if clearance else contour
    if marks:
        holes = unary_union([mark_footprint(m).buffer(clearance) for m in marks])
        allowed = allowed.difference(holes)

    half_w = width_factor * height * digits / 2
    half_h = height / 2
    sweeps: list[Polygon] = []
    for line in shapely.get_parts(allowed.boundary):
        coords = list(line.coords)
        for (x0, y0), (x1, y1) in zip(coords, coords[1:], strict=False):
            corners = [
                (x + dx, y + dy)
                for x, y in ((x0, y0), (x1, y1))
                for dx in (-half_w, half_w)
                for dy in (-half_h, half_h)
            ]
            sweeps.append(cast(Polygon, shapely.MultiPoint(corners).convex_hull))
    centres = allowed.difference(unary_union(sweeps)) if sweeps else allowed

    best: tuple[float, float, float] | None = None
    for part in shapely.get_parts(centres):
        if not isinstance(part, Polygon) or part.is_empty or part.area <= 0:
            continue
        point = polylabel(part, tolerance)
        reach = part.boundary.distance(point)
        if best is None or reach > best[2]:
            best = (point.x, point.y, reach)
    if best is not None:
        return NumberPlacement(best[0], best[1], True)

    point = polylabel(contour, tolerance)
    return NumberPlacement(point.x, point.y, False)


def largest_fitting_height(
    contour: Polygon,
    marks: Sequence[ReferenceMark],
    *,
    digits: int,
    ceiling: float,
    width_factor: float,
    clearance: float,
) -> float:
    """Return the tallest number, up to ``ceiling``, that fits clear of the cuts of a piece.

    A smaller number fits wherever a larger one does, so the height is found by halving. The
    result is a height that fits (``place_number`` says so), within 0.1% of ``ceiling`` of the
    tallest one. It is ``ceiling`` when that fits, and 0.0 when even a thousandth of it does not.
    """

    def fits(height: float) -> bool:
        return place_number(
            contour,
            marks,
            digits=digits,
            height=height,
            width_factor=width_factor,
            clearance=clearance,
        ).fits

    if fits(ceiling):
        return ceiling
    low, high = ceiling / 1000, ceiling
    if not fits(low):
        return 0.0
    for _ in range(12):
        middle = (low + high) / 2
        if fits(middle):
            low = middle
        else:
            high = middle
    return low
