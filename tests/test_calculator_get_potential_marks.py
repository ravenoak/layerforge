import math

import pytest

pytest.importorskip("shapely")
from hypothesis import given
from hypothesis import strategies as st
from shapely.geometry import Point, Polygon

from layerforge.models.reference_marks import (
    ReferenceMarkCalculator,
    ReferenceMarkConfig,
    ReferenceMarkManager,
)
from layerforge.models.slicing.slice import Slice


def create_slice(polygons, manager=None, cfg=None):
    manager = manager or ReferenceMarkManager(config=cfg)
    cfg = cfg or ReferenceMarkConfig()
    return Slice(0, 0.0, polygons, origin=(0, 0), mark_manager=manager, config=cfg)


def test_potential_marks_inside_polygon():
    square = Polygon([(0, 0), (100, 0), (100, 100), (0, 100)])
    cfg = ReferenceMarkConfig(min_distance=10)
    sl = create_slice([square], cfg=cfg)

    marks = ReferenceMarkCalculator.get_potential_marks(sl, [], config=cfg)
    assert len(marks) == 1
    x, y = marks[0]
    pt = Point(x, y)
    assert square.contains(pt)
    assert square.boundary.distance(pt) >= cfg.min_distance


def test_existing_mark_inherited():
    square = Polygon([(0, 0), (100, 0), (100, 100), (0, 100)])
    cfg = ReferenceMarkConfig(min_distance=10)
    sl = create_slice([square], cfg=cfg)

    marks = ReferenceMarkCalculator.get_potential_marks(sl, [(50, 50)], config=cfg)
    assert marks == [(50, 50)]


def test_sample_points_generate_multiple_unique_points():
    square = Polygon([(0, 0), (100, 0), (100, 100), (0, 100)])
    pts = ReferenceMarkCalculator._sample_points(square, samples=4)
    # should return centroid plus at least one other unique point
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
    cfg = ReferenceMarkConfig(min_distance=5)
    sl = create_slice([plate], cfg=cfg)

    (mark,) = ReferenceMarkCalculator.get_stable_marks(sl, [], config=cfg)
    assert plate.contains(Point(*mark))


def test_sample_points_stay_out_of_holes():
    plate = _plate_with_hole()
    for x, y in ReferenceMarkCalculator._sample_points(plate, samples=8):
        assert plate.contains(Point(x, y))


_COORD = st.floats(0, 30).map(lambda v: round(v, 3))


@given(
    stored=st.lists(st.tuples(_COORD, _COORD), max_size=4),
    tolerance=st.floats(1, 30).map(lambda v: round(v, 3)),
)
def test_chosen_points_are_stored_marks_or_out_of_snapping_range(stored, tolerance):
    """A point within the tolerance of a stored mark must be that mark (TR-10)."""
    square = Polygon([(0, 0), (30, 0), (30, 30), (0, 30)])
    cfg = ReferenceMarkConfig(min_distance=5, tolerance=tolerance)
    chosen = ReferenceMarkCalculator.get_stable_marks(create_slice([square], cfg=cfg), stored, cfg)

    new = [p for p in chosen if p not in stored]
    for x, y in new:
        assert all(math.hypot(x - sx, y - sy) > tolerance for sx, sy in stored)
    for i, (x1, y1) in enumerate(new):
        for x2, y2 in new[i + 1 :]:
            assert math.hypot(x1 - x2, y1 - y2) > tolerance
