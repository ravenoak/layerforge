"""The rotational symmetry test of a set of marks (TR-2).

Two layers stack in one way only if no turn other than none maps the marks they share onto
themselves. A mark is the same after a turn when its shape and size match, its centre lands
on a mark, and its angle matches modulo the symmetry order of its shape (TR-7).
"""

import math
from collections.abc import Sequence
from dataclasses import dataclass

from layerforge.domain.shapes.registry import shape_symmetry_order

from .reference_mark import ReferenceMark

_FULL_TURN = 2 * math.pi


@dataclass(frozen=True)
class RotationSymmetry:
    """The turns that map a set of marks onto itself.

    Attributes
    ----------
    centre : tuple of float, or None
        The centre of the turns: the centroid of the mark centres. ``None`` for an empty set.
    angles : tuple of float
        The turns other than none, in radians in (0, 2π), ascending.
    unlimited : bool
        True when every turn maps the set onto itself (marks that are all circles at one point,
        or no marks at all). ``angles`` is empty then.
    """

    centre: tuple[float, float] | None
    angles: tuple[float, ...]
    unlimited: bool = False

    @property
    def has_nonidentity(self) -> bool:
        """True when some turn other than none maps the set onto itself."""
        return self.unlimited or bool(self.angles)

    @property
    def order(self) -> int | None:
        """The turns that map the set onto itself, none included. ``None`` if unlimited."""
        return None if self.unlimited else len(self.angles) + 1


def rotation_symmetry(marks: Sequence[ReferenceMark], *, tolerance: float) -> RotationSymmetry:
    """Find the turns, about any centre, that map ``marks`` onto themselves.

    A turn fixes the centroid of the mark centres, so the centroid is the only centre to try.
    ``tolerance`` is a length: a position, a size and a mark's angle (as the movement of its
    edge, size / 2 times the angle) must each match within it. A set that maps onto itself
    within ``tolerance / 6`` is found. A mark listed twice (the same shape, size, angle and
    centre within ``tolerance``) counts once, as in TR-10. Two different marks closer than
    ``2 * tolerance`` cannot be told apart, and the answer for them is not defined.

    Parameters
    ----------
    marks : Sequence of ReferenceMark
        The marks two layers share.
    tolerance : float
        The match distance. It must be positive and finite: at zero, float error makes a set that
        has a symmetry read as having none, which is the unsafe answer.

    Returns
    -------
    RotationSymmetry
        The turns found.

    Raises
    ------
    ValueError
        If ``tolerance`` is not positive and finite, a mark has a value that is not finite, or
        a mark names a shape that is not registered.
    """
    if not (math.isfinite(tolerance) and tolerance > 0):
        raise ValueError(f"tolerance must be positive and finite, got {tolerance}")
    orders: dict[str, int | None] = {}
    for index, m in enumerate(marks):
        for field in ("x", "y", "size", "angle"):
            value = getattr(m, field)
            if not math.isfinite(value):
                raise ValueError(f"mark {index} has a {field} that is not finite: {value}")
        orders[m.shape] = shape_symmetry_order(m.shape)
    marks = _without_repeats(marks, orders, tolerance)
    if not marks:
        return RotationSymmetry(centre=None, angles=(), unlimited=True)

    cx = math.fsum(m.x for m in marks) / len(marks)
    cy = math.fsum(m.y for m in marks) / len(marks)
    centre = (cx, cy)
    farthest = max(marks, key=lambda m: math.hypot(m.x - cx, m.y - cy))
    reach = max(math.hypot(m.x - cx, m.y - cy) + m.size / 2 for m in marks)

    if math.hypot(farthest.x - cx, farthest.y - cy) > tolerance:
        base = math.atan2(farthest.y - cy, farthest.x - cx)
        candidates = [
            math.atan2(m.y - cy, m.x - cx) - base
            for m in marks
            if _same_kind(m, farthest, tolerance)
        ]
    else:
        anchor = next((m for m in marks if orders[m.shape] is not None), None)
        if anchor is None:
            return RotationSymmetry(centre=centre, angles=(), unlimited=True)
        order = orders[anchor.shape]
        assert order is not None
        candidates = [
            m.angle - anchor.angle + k * _FULL_TURN / order
            for m in marks
            if _same_kind(m, anchor, tolerance)
            for k in range(order)
        ]

    found: list[float] = []
    angle_tolerance = tolerance / max(reach, tolerance)
    for candidate in sorted(theta % _FULL_TURN for theta in candidates):
        if min(candidate, _FULL_TURN - candidate) <= angle_tolerance:
            continue
        if found and candidate - found[-1] <= angle_tolerance:
            continue
        if _maps_onto_itself(marks, orders, centre, candidate, tolerance):
            found.append(candidate)
    return RotationSymmetry(centre=centre, angles=tuple(found))


def _same_kind(a: ReferenceMark, b: ReferenceMark, tolerance: float) -> bool:
    return a.shape == b.shape and abs(a.size - b.size) <= tolerance


def _without_repeats(
    marks: Sequence[ReferenceMark], orders: dict[str, int | None], tolerance: float
) -> list[ReferenceMark]:
    """Drop a mark that repeats an earlier one (TR-10: the same shape, size, angle and centre)."""
    kept: list[ReferenceMark] = []
    for m in marks:
        repeats = any(
            _same_kind(m, k, tolerance)
            and math.hypot(m.x - k.x, m.y - k.y) <= tolerance
            and _angle_gap(m.angle, k.angle, orders[m.shape]) * m.size / 2 <= tolerance
            for k in kept
        )
        if not repeats:
            kept.append(m)
    return kept


def _angle_gap(a: float, b: float, order: int | None) -> float:
    """The smallest turn between two angles of a shape with symmetry ``order``."""
    if order is None:
        return 0.0
    period = _FULL_TURN / order
    gap = (a - b) % period
    return min(gap, period - gap)


def _maps_onto_itself(
    marks: Sequence[ReferenceMark],
    orders: dict[str, int | None],
    centre: tuple[float, float],
    theta: float,
    tolerance: float,
) -> bool:
    """True when turning every mark by ``theta`` about ``centre`` lands each on its own mark.

    ``unused`` holds the marks not yet claimed as another mark's image, and each match removes
    its mark from it (#204). Without that, two marks less than ``2 * tolerance`` apart could both
    be matched to the same image, so a turn that only sends one mark onto a shared spot would
    wrongly pass. See ``test_the_one_to_one_match_rejects_a_double_use_of_one_mark``.
    """
    cx, cy = centre
    cos, sin = math.cos(theta), math.sin(theta)
    unused = list(marks)
    for m in marks:
        dx, dy = m.x - cx, m.y - cy
        x, y = cx + dx * cos - dy * sin, cy + dx * sin + dy * cos
        best = None
        best_distance = tolerance
        for other in unused:
            if not _same_kind(m, other, tolerance):
                continue
            if _angle_gap(m.angle + theta, other.angle, orders[m.shape]) * m.size / 2 > tolerance:
                continue
            distance = math.hypot(other.x - x, other.y - y)
            if distance <= best_distance:
                best, best_distance = other, distance
        if best is None:
            return False
        unused.remove(best)
    return True
