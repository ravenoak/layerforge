import pytest

pytest.importorskip("shapely")

from shapely.geometry import Polygon, Point

from layerforge.models.reference_marks import ReferenceMarkManager, ReferenceMarkService, ReferenceMarkConfig
from layerforge.models.slicing import Slice


def test_inherit_mark_within_polygon():
    square = Polygon([(0, 0), (100, 0), (100, 100), (0, 100)])
    manager = ReferenceMarkManager()
    manager.add_or_update_mark(50, 50, "circle", 3)
    cfg = ReferenceMarkConfig(min_distance=10)
    sl = Slice(0, 0.0, [square], origin=(0, 0), mark_manager=manager, config=cfg)
    ReferenceMarkService.process_slice(sl)
    assert len(sl.ref_marks) == 1
    assert sl.ref_marks[0].x == 50
    assert sl.ref_marks[0].y == 50


def test_generate_mark_respects_boundary():
    square = Polygon([(0, 0), (100, 0), (100, 100), (0, 100)])
    manager = ReferenceMarkManager()
    cfg = ReferenceMarkConfig(min_distance=10)
    sl = Slice(1, 0.0, [square], origin=(0, 0), mark_manager=manager, config=cfg)
    ReferenceMarkService.process_slice(sl)
    assert len(sl.ref_marks) == 1
    pt = Point(sl.ref_marks[0].x, sl.ref_marks[0].y)
    assert square.contains(pt)
    assert square.boundary.distance(pt) >= 10
