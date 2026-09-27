"""The rotational symmetry test of a set of marks (TR-2, #90).

A turn about any centre that maps the marks onto themselves, with each mark's shape, size
and angle, lets two layers stack a second way. `rotation_symmetry` finds those turns.
"""

import math

import pytest

from layerforge.domain.shapes.registry import shape_symmetry_order
from layerforge.models.reference_marks import ReferenceMark, rotation_symmetry

TOL = 1e-6


def mark(x: float, y: float, shape: str, *, size: float = 3.0, angle: float = 0.0):
    return ReferenceMark(x=x, y=y, shape=shape, size=size, angle=angle)


def ring(n: int, shape: str, radius: float = 10.0, *, turn: float = 0.0, outward: bool = False):
    """n marks of one shape on a circle about the origin, an equal turn apart."""
    step = 2 * math.pi / n
    return [
        mark(
            radius * math.cos(k * step),
            radius * math.sin(k * step),
            shape,
            angle=turn + (k * step if outward else 0.0),
        )
        for k in range(n)
    ]


def turns(marks) -> list[int]:
    """The non-identity turns in whole degrees."""
    return [round(math.degrees(a)) for a in rotation_symmetry(marks, tolerance=TOL).angles]


def test_a_shape_states_its_symmetry_order() -> None:
    assert shape_symmetry_order("circle") is None
    assert shape_symmetry_order("square") == 4
    assert shape_symmetry_order("triangle") == 1
    assert shape_symmetry_order("arrow") == 1


def test_an_unknown_shape_has_no_symmetry_order() -> None:
    with pytest.raises(ValueError, match="hexagon"):
        shape_symmetry_order("hexagon")


CASES = {
    "one triangle": ([mark(0, 0, "triangle")], []),
    "one square": ([mark(0, 0, "square")], [90, 180, 270]),
    "one square at 45 degrees": ([mark(0, 0, "square", angle=math.pi / 4)], [90, 180, 270]),
    "two identical circles": ([mark(-5, 0, "circle"), mark(5, 0, "circle")], [180]),
    "a circle and a square": ([mark(-5, 0, "circle"), mark(5, 0, "square")], []),
    "three circles, all sides different": (
        [mark(0, 0, "circle"), mark(4, 0, "circle"), mark(0, 3, "circle")],
        [],
    ),
    "three circles in an equilateral triangle": (ring(3, "circle"), [120, 240]),
    "two triangles with one angle": ([mark(-5, 0, "triangle"), mark(5, 0, "triangle")], []),
    "two triangles pointing apart": (
        [mark(5, 0, "triangle"), mark(-5, 0, "triangle", angle=math.pi)],
        [180],
    ),
    "two squares with one angle": ([mark(-5, 0, "square"), mark(5, 0, "square")], [180]),
    "two squares, 45 degrees apart": (
        [mark(-5, 0, "square"), mark(5, 0, "square", angle=math.pi / 4)],
        [],
    ),
    "two circles of different size": (
        [mark(-5, 0, "circle", size=3), mark(5, 0, "circle", size=4)],
        [],
    ),
    "a square angle just under a full turn": (
        [mark(-5, 0, "square"), mark(5, 0, "square", angle=2 * math.pi - 1e-9)],
        [180],
    ),
    "a triangle angle just under one and a half turns": (
        [mark(5, 0, "triangle"), mark(-5, 0, "triangle", angle=3 * math.pi - 1e-9)],
        [180],
    ),
    "four squares at the corners": (
        [mark(x, y, "square", angle=math.pi / 8) for x in (-5, 5) for y in (-5, 5)],
        [90, 180, 270],
    ),
    "four triangles with one angle": (
        [mark(x, y, "triangle") for x in (-5, 5) for y in (-5, 5)],
        [],
    ),
    "four triangles pointing outward": (ring(4, "triangle", outward=True), [90, 180, 270]),
    "five arrows pointing outward": (ring(5, "arrow", outward=True), [72, 144, 216, 288]),
    "six circles in a hexagon": (ring(6, "circle"), [60, 120, 180, 240, 300]),
    "a square in the middle of four circles": (
        [mark(0, 0, "square"), *ring(4, "circle")],
        [90, 180, 270],
    ),
    "a triangle in the middle of four circles": ([mark(0, 0, "triangle"), *ring(4, "circle")], []),
    "a square in the middle of three circles": ([mark(0, 0, "square"), *ring(3, "circle")], []),
    "a circle in the middle of three circles": (
        [mark(0, 0, "circle"), *ring(3, "circle")],
        [120, 240],
    ),
    "a square in the middle of two circles": (
        [mark(0, 0, "square"), mark(-5, 0, "circle"), mark(5, 0, "circle")],
        [180],
    ),
    "a circle and a square in one place": (
        [mark(0, 0, "circle"), mark(0, 0, "square")],
        [90, 180, 270],
    ),
    "two nested pairs of circles on one line": (
        [
            mark(-5, 0, "circle"),
            mark(5, 0, "circle"),
            mark(-10, 0, "circle"),
            mark(10, 0, "circle"),
        ],
        [180],
    ),
    "two triangles in one place, half a turn apart": (
        [mark(0, 0, "triangle"), mark(0, 0, "triangle", angle=math.pi)],
        [180],
    ),
    "a set far from the origin": (
        [mark(10000 - 5, 10000, "circle"), mark(10000 + 5, 10000, "circle")],
        [180],
    ),
}


@pytest.mark.parametrize("marks, expected", CASES.values(), ids=CASES.keys())
def test_the_turns_that_map_the_marks_onto_themselves(marks, expected) -> None:
    assert turns(marks) == expected


def test_a_mark_listed_twice_counts_once() -> None:
    """TR-10: a mark with the same shape, size, angle and centre is the same mark."""
    corners = ring(4, "circle")
    repeated = [corners[0], corners[0], corners[1], corners[2], corners[2], corners[3]]
    assert turns(repeated) == turns(corners) == [90, 180, 270]


def test_a_mark_listed_twice_within_the_tolerance_counts_once() -> None:
    corners = ring(4, "circle")
    near = mark(corners[0].x + 4e-7, corners[0].y, "circle")
    assert turns([corners[0], near, *corners[1:]]) == [90, 180, 270]


def test_one_circle_has_unlimited_symmetry() -> None:
    result = rotation_symmetry([mark(0, 0, "circle")], tolerance=TOL)
    assert result.unlimited
    assert result.has_nonidentity
    assert result.order is None


def test_two_circles_at_one_place_have_unlimited_symmetry() -> None:
    marks = [mark(0, 0, "circle", size=3), mark(0, 0, "circle", size=3)]
    assert rotation_symmetry(marks, tolerance=TOL).unlimited


def test_an_empty_set_has_unlimited_symmetry() -> None:
    result = rotation_symmetry([], tolerance=TOL)
    assert result.unlimited
    assert result.centre is None


def test_no_symmetry_is_order_one() -> None:
    result = rotation_symmetry([mark(0, 0, "triangle")], tolerance=TOL)
    assert not result.has_nonidentity
    assert result.order == 1
    assert not result.unlimited


def test_the_order_counts_the_identity() -> None:
    assert rotation_symmetry(ring(3, "circle"), tolerance=TOL).order == 3


def test_the_centre_is_the_centroid_of_the_marks() -> None:
    result = rotation_symmetry([mark(1, 2, "circle"), mark(5, 2, "circle")], tolerance=TOL)
    assert result.centre == pytest.approx((3.0, 2.0))


def test_a_small_shift_within_the_tolerance_keeps_the_symmetry() -> None:
    marks = ring(3, "circle")
    marks[0] = mark(marks[0].x + 1e-7, marks[0].y, "circle")
    assert rotation_symmetry(marks, tolerance=TOL).order == 3


def test_a_shift_beyond_the_tolerance_breaks_the_symmetry() -> None:
    marks = ring(3, "circle")
    marks[0] = mark(marks[0].x + 1e-5, marks[0].y, "circle")
    assert not rotation_symmetry(marks, tolerance=TOL).has_nonidentity


@pytest.mark.parametrize("tolerance", [0.0, -1.0, math.nan, math.inf])
def test_a_tolerance_that_is_not_positive_and_finite_is_refused(tolerance: float) -> None:
    with pytest.raises(ValueError, match="tolerance"):
        rotation_symmetry([mark(0, 0, "triangle")], tolerance=tolerance)


@pytest.mark.parametrize("field", ["x", "y", "size", "angle"])
@pytest.mark.parametrize("value", [math.nan, math.inf])
def test_a_mark_with_a_value_that_is_not_finite_is_refused(field: str, value: float) -> None:
    bad = mark(0, 0, "triangle")
    setattr(bad, field, value)
    with pytest.raises(ValueError, match=field):
        rotation_symmetry([mark(5, 0, "triangle"), bad], tolerance=TOL)


def test_a_mark_with_an_unknown_shape_is_refused() -> None:
    with pytest.raises(ValueError, match="hexagon"):
        rotation_symmetry([mark(0, 0, "hexagon")], tolerance=TOL)
