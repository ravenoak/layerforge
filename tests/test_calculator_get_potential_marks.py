import pytest
pytest.importorskip("shapely")
from shapely.geometry import Polygon, Point
import random

from layerforge.models.reference_marks import (
    ReferenceMarkCalculator,
    ReferenceMarkManager,
    ReferenceMarkConfig,
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
    random.seed(0)
    square = Polygon([(0, 0), (100, 0), (100, 100), (0, 100)])
    pts = ReferenceMarkCalculator._sample_points(square, samples=4)
    # should return centroid plus at least one other unique point
    assert len(pts) >= 2
    assert len(set(pts)) == len(pts)
    for x, y in pts:
        assert square.contains(Point(x, y))


def test_sample_points_triangle_diversity():
    random.seed(1)
    triangle = Polygon([(0, 0), (50, 100), (100, 0)])
    pts = ReferenceMarkCalculator._sample_points(triangle, samples=4)
    assert len(pts) >= 2
    assert len(set(pts)) == len(pts)
    for x, y in pts:
        assert triangle.contains(Point(x, y))
