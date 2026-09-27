"""An independent oracle for `rotation_symmetry` (TR-2, #91).

The symmetry test is the core safety check of the tool: if it misses a turn, two layers stack a
second way and nobody knows until the sheet is cut. This file finds the same answer another way
and asserts that the two agree.

`rotation_symmetry` reasons about the centroid and one candidate turn per mark. The oracle uses
neither. It takes the first mark and the mark farthest from it, tries every rigid motion (a turn
and a shift) that carries that pair onto a pair of marks of the same kinds and the same distance
apart, and counts the motions that carry the whole set onto itself. It shares no code with the
function under test, and keeps its own table of symmetry orders.
"""

import math
from collections.abc import Sequence

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from layerforge.models.reference_marks import ReferenceMark, rotation_symmetry

from .test_rotation_symmetry import CASES, mark

TOL = 1e-6
TWO_PI = 2 * math.pi
ORDERS: dict[str, int | None] = {"circle": None, "square": 4, "triangle": 1, "arrow": 1}


def _gap(a: float, b: float, shape: str) -> float:
    """The smallest turn between two angles of a shape, whose looks repeat every 2π / order."""
    order = ORDERS[shape]
    if order is None:
        return 0.0
    period = TWO_PI / order
    gap = (a - b) % period
    return min(gap, period - gap)


def _same_kind(a: ReferenceMark, b: ReferenceMark) -> bool:
    return a.shape == b.shape and abs(a.size - b.size) <= TOL


def _carries_onto_itself(
    marks: Sequence[ReferenceMark], theta: float, shift: tuple[float, float]
) -> bool:
    """True if turning by theta about the origin, then shifting, gives each mark its own partner."""
    cos, sin = math.cos(theta), math.sin(theta)
    partners: set[int] = set()
    for m in marks:
        x = m.x * cos - m.y * sin + shift[0]
        y = m.x * sin + m.y * cos + shift[1]
        hits = [
            i
            for i, other in enumerate(marks)
            if _same_kind(m, other)
            and math.hypot(other.x - x, other.y - y) <= TOL
            and _gap(m.angle + theta, other.angle, m.shape) * m.size / 2 <= TOL
        ]
        if len(hits) != 1 or hits[0] in partners:
            return False
        partners.add(hits[0])
    return True


def oracle_order(marks: Sequence[ReferenceMark]) -> int | None:
    """The number of turns that map the marks onto themselves, none included; None if unlimited."""
    first = marks[0]
    far = max(marks, key=lambda m: math.hypot(m.x - first.x, m.y - first.y))
    span = math.hypot(far.x - first.x, far.y - first.y)
    motions: list[tuple[float, tuple[float, float]]] = []
    if span <= TOL:
        # Every mark sits in one place. All circles turn into themselves by any angle.
        if all(m.shape == "circle" for m in marks):
            return None
        # The angles of the generated marks are multiples of π/4, so any turn that works is too.
        for k in range(8):
            theta = k * math.pi / 4
            shift = (
                first.x - (first.x * math.cos(theta) - first.y * math.sin(theta)),
                first.y - (first.x * math.sin(theta) + first.y * math.cos(theta)),
            )
            motions.append((theta, shift))
    else:
        base = math.atan2(far.y - first.y, far.x - first.x)
        for b1 in marks:
            for b2 in marks:
                if not (_same_kind(first, b1) and _same_kind(far, b2)):
                    continue
                if abs(math.hypot(b2.x - b1.x, b2.y - b1.y) - span) > 3 * TOL:
                    continue
                theta = math.atan2(b2.y - b1.y, b2.x - b1.x) - base
                shift = (
                    b1.x - (first.x * math.cos(theta) - first.y * math.sin(theta)),
                    b1.y - (first.x * math.sin(theta) + first.y * math.cos(theta)),
                )
                motions.append((theta, shift))
    found: list[float] = []
    for theta, shift in motions:
        if not _carries_onto_itself(marks, theta, shift):
            continue
        turn = theta % TWO_PI
        if not any(min(abs(turn - t), TWO_PI - abs(turn - t)) < 1e-6 for t in found):
            found.append(turn)
    return len(found)


# The generated marks sit on a whole-number grid, with sizes 2 and 3 and angles that are
# multiples of π/4. No coordinate is tiny, and no two marks are near enough to sit at the edge of
# the tolerance.
COORD = st.integers(-20, 20).map(float)
SIZE = st.sampled_from([2.0, 3.0])
SHAPE = st.sampled_from(list(ORDERS))
ANGLE_STEP = st.integers(0, 7)


def _mark_from(x: float, y: float, shape: str, size: float, step: int) -> ReferenceMark:
    return ReferenceMark(x=x, y=y, shape=shape, size=size, angle=step * math.pi / 4)


MARK = st.builds(_mark_from, COORD, COORD, SHAPE, SIZE, ANGLE_STEP)


def _key(m: ReferenceMark) -> tuple[float, float, str, float, int]:
    """Two marks with one key are one mark: a circle has no angle, a square repeats every π/2."""
    order = ORDERS[m.shape]
    step = round(m.angle / (math.pi / 4))
    return (m.x, m.y, m.shape, m.size, 0 if order is None else step % (8 // order))


RANDOM_SETS = st.lists(MARK, min_size=1, max_size=6, unique_by=_key)


def _the_same_mark_twice(marks: Sequence[ReferenceMark]) -> bool:
    for i, a in enumerate(marks):
        for b in marks[:i]:
            if (
                _same_kind(a, b)
                and math.hypot(a.x - b.x, a.y - b.y) < 1e-3
                and _gap(a.angle, b.angle, a.shape) * a.size / 2 < 1e-2
            ):
                return True
    return False


@st.composite
def symmetric_sets(draw: st.DrawFn) -> list[ReferenceMark]:
    """A motif of one or two marks turned n times about a centre, and maybe a mark at the centre.

    The set is not always symmetric: a triangle at the centre, or a square when n does not divide
    4, breaks it. The agreement test wants both kinds.
    """
    n = draw(st.sampled_from([2, 3, 4, 5, 6]))
    centre = (draw(COORD), draw(COORD))
    motif = draw(
        st.lists(
            st.tuples(st.integers(-10, 10), st.integers(-10, 10), SHAPE, SIZE, ANGLE_STEP),
            min_size=1,
            max_size=2,
        )
    )
    if len(motif) == 2 and draw(st.booleans()):
        # Put the second mark on the ray of the first, twice as far out: two marks then give
        # one candidate turn between them.
        dx, dy, *_ = motif[0]
        motif[1] = (2 * dx, 2 * dy, *motif[1][2:])
    assume(all((dx, dy) != (0, 0) for dx, dy, *_ in motif))
    marks: list[ReferenceMark] = []
    for k in range(n):
        turn = k * TWO_PI / n
        for dx, dy, shape, size, step in motif:
            marks.append(
                ReferenceMark(
                    x=centre[0] + dx * math.cos(turn) - dy * math.sin(turn),
                    y=centre[1] + dx * math.sin(turn) + dy * math.cos(turn),
                    shape=shape,
                    size=size,
                    angle=step * math.pi / 4 + turn,
                )
            )
    if draw(st.booleans()):
        marks.append(_mark_from(centre[0], centre[1], draw(SHAPE), draw(SIZE), draw(ANGLE_STEP)))
    assume(not _the_same_mark_twice(marks))
    return marks


@st.composite
def nearly_symmetric_sets(draw: st.DrawFn) -> list[ReferenceMark]:
    """A symmetric set with one mark moved, turned, swapped for another shape, or resized."""
    marks = draw(symmetric_sets())
    i = draw(st.integers(0, len(marks) - 1))
    m = marks[i]
    change = draw(st.sampled_from(["move", "turn", "shape", "size"]))
    if change == "move":
        marks[i] = ReferenceMark(m.x + 1.0, m.y, m.shape, m.size, m.angle)
    elif change == "turn":
        marks[i] = ReferenceMark(m.x, m.y, m.shape, m.size, m.angle + math.pi / 7)
    elif change == "shape":
        other = draw(SHAPE.filter(lambda s: s != m.shape))
        marks[i] = ReferenceMark(m.x, m.y, other, m.size, m.angle)
    else:
        marks[i] = ReferenceMark(m.x, m.y, m.shape, 5.0 - m.size, m.angle)
    assume(not _the_same_mark_twice(marks))
    return marks


@settings(max_examples=300, deadline=None)
@given(st.one_of(RANDOM_SETS, symmetric_sets(), nearly_symmetric_sets()))
def test_the_function_and_the_oracle_agree(marks: list[ReferenceMark]) -> None:
    result = rotation_symmetry(marks, tolerance=TOL)
    assert result.order == oracle_order(marks), marks


@pytest.mark.parametrize("marks, expected", CASES.values(), ids=CASES.keys())
def test_the_oracle_and_the_function_give_the_known_answers(
    marks: list[ReferenceMark], expected: list[int]
) -> None:
    assert oracle_order(marks) == len(expected) + 1
    assert rotation_symmetry(marks, tolerance=TOL).order == len(expected) + 1


def test_the_oracle_calls_circles_in_one_place_unlimited() -> None:
    assert oracle_order([mark(0, 0, "circle")]) is None


@settings(max_examples=100, deadline=None)
@given(st.one_of(RANDOM_SETS, symmetric_sets()), st.data())
def test_a_mark_listed_twice_changes_nothing(
    marks: list[ReferenceMark], data: st.DataObject
) -> None:
    again = data.draw(st.sampled_from(marks))
    assert rotation_symmetry([*marks, again], tolerance=TOL).order == oracle_order(marks)


@settings(max_examples=100, deadline=None)
@given(symmetric_sets(), st.data())
def test_a_set_that_is_symmetric_within_a_fraction_of_the_tolerance_is_still_found(
    marks: list[ReferenceMark], data: st.DataObject
) -> None:
    assume(oracle_order(marks) != 1)  # start from a set that really is symmetric
    jitter = st.floats(-TOL / 8, TOL / 8)
    moved = [
        ReferenceMark(m.x + data.draw(jitter), m.y + data.draw(jitter), m.shape, m.size, m.angle)
        for m in marks
    ]
    assert rotation_symmetry(moved, tolerance=TOL).has_nonidentity
