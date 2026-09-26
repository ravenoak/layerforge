import logging
import math

import pytest

pytest.importorskip("shapely")
from shapely.geometry import Polygon

from layerforge.models.reference_marks import (
    ReferenceMark,
    ReferenceMarkCalculator,
    ReferenceMarkConfig,
    ReferenceMarkManager,
    ReferenceMarkService,
)
from layerforge.models.slicing.slice import Slice


def test_new_mark_added_to_manager():
    square = Polygon([(0, 0), (100, 0), (100, 100), (0, 100)])
    manager = ReferenceMarkManager()
    cfg = ReferenceMarkConfig(min_distance=10)
    sl = Slice(0, 0.0, [square], mark_manager=manager, config=cfg, layer_height=3.0)
    ReferenceMarkService.process_slice(sl)
    assert len(sl.ref_marks) == 1
    # manager should now contain the new mark
    assert len(manager.marks) == 1
    assert manager.marks[0].x == sl.ref_marks[0].x
    assert manager.marks[0].y == sl.ref_marks[0].y


def test_inherited_mark_keeps_angle_and_color():
    square = Polygon([(0, 0), (100, 0), (100, 100), (0, 100)])
    manager = ReferenceMarkManager()
    cfg1 = ReferenceMarkConfig(min_distance=10, angle=math.pi / 4, color="red")
    sl1 = Slice(0, 0.0, [square], mark_manager=manager, config=cfg1, layer_height=3.0)
    ReferenceMarkService.process_slice(sl1)
    assert sl1.ref_marks[0].angle == math.pi / 4
    assert sl1.ref_marks[0].color == "red"

    cfg2 = ReferenceMarkConfig(min_distance=10, angle=math.pi / 2, color="blue")
    sl2 = Slice(1, 0.0, [square], mark_manager=manager, config=cfg2, layer_height=3.0)
    ReferenceMarkService.process_slice(sl2)
    assert sl2.ref_marks[0].angle == math.pi / 4
    assert sl2.ref_marks[0].color == "red"
    assert manager.marks[0].angle == math.pi / 4
    assert manager.marks[0].color == "red"


def test_warning_when_a_contour_gets_no_mark(caplog):
    small = Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])
    cfg = ReferenceMarkConfig(min_distance=10)
    sl = Slice(
        3,
        0.0,
        [small],
        mark_manager=ReferenceMarkManager(),
        config=cfg,
        layer_height=3.0,
    )
    with caplog.at_level(logging.WARNING):
        ReferenceMarkService.process_slice(sl)

    assert sl.ref_marks == []
    (record,) = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert "slice 3" in record.getMessage()
    assert "--mark-min-distance" in record.getMessage()


def test_no_warning_when_every_contour_has_a_mark(caplog):
    square = Polygon([(0, 0), (100, 0), (100, 100), (0, 100)])
    cfg = ReferenceMarkConfig(min_distance=10)
    sl = Slice(
        0,
        0.0,
        [square],
        mark_manager=ReferenceMarkManager(),
        config=cfg,
        layer_height=3.0,
    )
    with caplog.at_level(logging.WARNING):
        ReferenceMarkService.process_slice(sl)

    assert len(sl.ref_marks) == 1
    assert not [r for r in caplog.records if r.levelno == logging.WARNING]


def _stub_chosen_points(monkeypatch, points):
    """Make the calculator choose ``points``, as if sampling had landed there."""
    monkeypatch.setattr(
        ReferenceMarkCalculator,
        "get_stable_marks",
        staticmethod(lambda layer, existing, config=None: list(points)),
    )


def test_point_near_a_stored_mark_takes_its_coordinates(monkeypatch):
    square = Polygon([(0, 0), (100, 0), (100, 100), (0, 100)])
    manager = ReferenceMarkManager()
    manager.marks = [ReferenceMark(x=20, y=50, shape="square", size=4, angle=1.0, color="red")]
    _stub_chosen_points(monkeypatch, [(23, 50)])
    sl = Slice(
        1,
        0.0,
        [square],
        mark_manager=manager,
        config=ReferenceMarkConfig(tolerance=10),
        layer_height=3.0,
    )

    sl.process_reference_marks()

    (mark,) = sl.ref_marks
    assert (mark.x, mark.y) == (20, 50)
    assert (mark.shape, mark.size, mark.angle, mark.color) == ("square", 4, 1.0, "red")
    assert len(manager.marks) == 1


def test_point_between_two_stored_marks_takes_the_nearer_one(monkeypatch):
    square = Polygon([(0, 0), (100, 0), (100, 100), (0, 100)])
    manager = ReferenceMarkManager()
    manager.marks = [
        ReferenceMark(x=5, y=50, shape="circle", size=3),
        ReferenceMark(x=12, y=50, shape="square", size=3),
    ]
    _stub_chosen_points(monkeypatch, [(10, 50)])
    sl = Slice(
        1,
        0.0,
        [square],
        mark_manager=manager,
        config=ReferenceMarkConfig(tolerance=10),
        layer_height=3.0,
    )

    sl.process_reference_marks()

    (mark,) = sl.ref_marks
    assert (mark.x, mark.y, mark.shape) == (12, 50, "square")


def test_unusable_stored_mark_is_not_reused_at_a_nearby_place():
    # The stored mark lies 5 from the edge, closer than min_distance, so this
    # slice cannot inherit it. Marks chosen here must not sit within the
    # tolerance of it, or the same mark would be at two places.
    small = Polygon([(0, 0), (30, 0), (30, 30), (0, 30)])
    manager = ReferenceMarkManager()
    manager.marks = [ReferenceMark(x=15, y=25, shape="square", size=4)]
    cfg = ReferenceMarkConfig(min_distance=10, tolerance=10)
    sl = Slice(1, 0.0, [small], mark_manager=manager, config=cfg, layer_height=3.0)

    ReferenceMarkService.process_slice(sl)

    for mark in sl.ref_marks:
        assert math.hypot(mark.x - 15, mark.y - 25) > 10
    assert len(manager.marks) == 1 + len(sl.ref_marks)


def test_the_slice_and_the_store_snap_with_the_same_tolerance():
    """#108 item 1: one source. The slice's tolerance decides, also when adding to the store.

    The stored square at (0, 30) lies outside the contour, so the calculator still picks the
    centre (0, 0). That is 30 from the square: outside the slice's tolerance of 0.3, inside
    the manager's 40. The new mark must be stored as a new mark, and the square must stay.
    """
    manager = ReferenceMarkManager(config=ReferenceMarkConfig(tolerance=40))
    manager.marks.append(ReferenceMark(0, 30, "square", 3))
    cfg = ReferenceMarkConfig(tolerance=0.3, min_distance=1)
    contour = Polygon([(-20, -20), (20, -20), (20, 20), (-20, 20)])
    sl = Slice(0, 0.0, [contour], mark_manager=manager, config=cfg, layer_height=3.0)
    sl.process_reference_marks()
    assert [(m.x, m.y) for m in sl.ref_marks] == [(0, 0)]
    assert [(m.shape, m.x, m.y) for m in manager.marks] == [("square", 0, 30), ("circle", 0, 0)]
