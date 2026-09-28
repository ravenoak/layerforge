import math

import pytest

pytest.importorskip("shapely")
from hypothesis import given
from hypothesis import strategies as st
from shapely.geometry import Point, Polygon

from layerforge.models.reference_marks import ReferenceMark, ReferenceMarkCalculator


def test_choosing_in_a_square_stays_inside_it():
    square = Polygon([(0, 0), (100, 0), (100, 100), (0, 100)])
    mark = ReferenceMarkCalculator.choose_mark_for_pair(
        square,
        [square],
        [],
        [],
        min_distance=10,
        min_web=0,
        tolerance=1,
        available_shapes=["circle"],
        size=3,
        angle=0.0,
    )
    assert mark is not None
    assert square.contains(Point(mark.x, mark.y))
    assert square.boundary.distance(Point(mark.x, mark.y)) >= 10


def test_a_candidate_at_the_right_place_is_reused():
    square = Polygon([(0, 0), (100, 0), (100, 100), (0, 100)])
    candidate = ReferenceMark(x=50, y=50, shape="circle", size=3)
    mark = ReferenceMarkCalculator.choose_mark_for_pair(
        square,
        [square],
        [candidate],
        [],
        min_distance=10,
        min_web=0,
        tolerance=1,
        available_shapes=["circle"],
        size=3,
        angle=0.0,
    )
    assert mark is candidate


def test_sample_points_generate_multiple_unique_points():
    square = Polygon([(0, 0), (100, 0), (100, 100), (0, 100)])
    pts = ReferenceMarkCalculator._sample_points(square, samples=4)
    assert len(pts) >= 2
    assert len(set(pts)) == len(pts)
    for x, y in pts:
        assert square.contains(Point(x, y))


def test_sample_points_triangle_diversity():
    triangle = Polygon([(0, 0), (50, 100), (100, 0)])
    pts = ReferenceMarkCalculator._sample_points(triangle, samples=4)
    assert len(pts) >= 2
    assert len(set(pts)) == len(pts)
    for x, y in pts:
        assert triangle.contains(Point(x, y))


def test_sample_points_are_deterministic():
    triangle = Polygon([(0, 0), (50, 100), (100, 0)])
    first = ReferenceMarkCalculator._sample_points(triangle, samples=4)
    second = ReferenceMarkCalculator._sample_points(triangle, samples=4)
    assert first == second


def _plate_with_hole() -> Polygon:
    """A 100 x 100 plate with a 60 x 60 hole, so its centroid is in the hole."""
    hole = [(20, 20), (80, 20), (80, 80), (20, 80)]
    return Polygon([(0, 0), (100, 0), (100, 100), (0, 100)], [hole])


def test_marks_avoid_holes():
    plate = _plate_with_hole()
    mark = ReferenceMarkCalculator.choose_mark_for_pair(
        plate,
        [plate],
        [],
        [],
        min_distance=5,
        min_web=0,
        tolerance=1,
        available_shapes=["circle"],
        size=3,
        angle=0.0,
    )
    assert mark is not None
    assert plate.contains(Point(mark.x, mark.y))


def test_sample_points_stay_out_of_holes():
    plate = _plate_with_hole()
    for x, y in ReferenceMarkCalculator._sample_points(plate, samples=8):
        assert plate.contains(Point(x, y))


class _FailsOnSecondContains:
    """Wraps a polygon. Its `contains` works for the centroid test and then raises.

    A subclass of `Polygon` does not work here: shapely builds a plain `Polygon`.
    """

    def __init__(self, polygon: Polygon):
        self._polygon = polygon
        self.calls = 0

    def __getattr__(self, name):
        return getattr(self._polygon, name)

    def contains(self, other):
        self.calls += 1
        if self.calls > 1:
            raise RuntimeError("shapely failed")
        return self._polygon.contains(other)


def test_an_error_from_the_candidate_test_reaches_the_caller():
    """It used to read as "outside", so an error hid as "no mark fits" (#171)."""
    poly = _FailsOnSecondContains(Polygon([(0, 0), (100, 0), (100, 100), (0, 100)]))
    with pytest.raises(RuntimeError, match="shapely failed"):
        ReferenceMarkCalculator._sample_points(poly, samples=4)  # pyright: ignore[reportArgumentType]
    assert poly.calls == 2


@pytest.mark.parametrize(
    "poly",
    [
        Polygon([(0, 0), (10, 10), (10, 0), (0, 10)]),  # a bow-tie, not valid
        Polygon([(0, 0), (5, 0), (10, 0)]),  # no area
        Polygon(),  # empty
    ],
    ids=["bow-tie", "no-area", "empty"],
)
def test_sample_points_of_a_degenerate_polygon_do_not_raise(poly):
    """The `except` around the candidate test guarded nothing that these reach (#171)."""
    assert isinstance(ReferenceMarkCalculator._sample_points(poly, samples=4), list)


_COORD = st.floats(0, 30).map(lambda v: round(v, 3))


@given(
    stored=st.lists(st.tuples(_COORD, _COORD), max_size=4),
    tolerance=st.floats(1, 30).map(lambda v: round(v, 3)),
)
def test_a_new_point_is_stored_marks_or_out_of_snapping_range(stored, tolerance):
    """A point within the tolerance of a stored mark must be that mark (TR-10)."""
    square = Polygon([(0, 0), (30, 0), (30, 30), (0, 30)])
    candidates = [ReferenceMark(x=x, y=y, shape="circle", size=1) for x, y in stored]
    mark = ReferenceMarkCalculator.choose_mark_for_pair(
        square,
        [square],
        candidates,
        [],
        min_distance=5,
        min_web=0,
        tolerance=tolerance,
        available_shapes=["circle"],
        size=1,
        angle=0.0,
    )
    if mark is None or (mark.x, mark.y) in stored:
        return
    assert all(math.hypot(mark.x - sx, mark.y - sy) > tolerance for sx, sy in stored)
