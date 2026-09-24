import logging
import math

import pytest

pytest.importorskip("shapely")
from shapely.geometry import Polygon

from layerforge.models.reference_marks import (
    ReferenceMarkConfig,
    ReferenceMarkManager,
    ReferenceMarkService,
)
from layerforge.models.slicing.slice import Slice


def test_new_mark_added_to_manager():
    square = Polygon([(0, 0), (100, 0), (100, 100), (0, 100)])
    manager = ReferenceMarkManager()
    cfg = ReferenceMarkConfig(min_distance=10)
    sl = Slice(0, 0.0, [square], origin=(0, 0), mark_manager=manager, config=cfg)
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
    sl1 = Slice(0, 0.0, [square], origin=(0, 0), mark_manager=manager, config=cfg1)
    ReferenceMarkService.process_slice(sl1)
    assert sl1.ref_marks[0].angle == math.pi / 4
    assert sl1.ref_marks[0].color == "red"

    cfg2 = ReferenceMarkConfig(min_distance=10, angle=math.pi / 2, color="blue")
    sl2 = Slice(1, 0.0, [square], origin=(0, 0), mark_manager=manager, config=cfg2)
    ReferenceMarkService.process_slice(sl2)
    assert sl2.ref_marks[0].angle == math.pi / 4
    assert sl2.ref_marks[0].color == "red"
    assert manager.marks[0].angle == math.pi / 4
    assert manager.marks[0].color == "red"


def test_warning_when_a_contour_gets_no_mark(caplog):
    small = Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])
    cfg = ReferenceMarkConfig(min_distance=10)
    sl = Slice(3, 0.0, [small], origin=(0, 0), mark_manager=ReferenceMarkManager(), config=cfg)
    with caplog.at_level(logging.WARNING):
        ReferenceMarkService.process_slice(sl)

    assert sl.ref_marks == []
    (record,) = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert "slice 3" in record.getMessage()
    assert "--mark-min-distance" in record.getMessage()


def test_no_warning_when_every_contour_has_a_mark(caplog):
    square = Polygon([(0, 0), (100, 0), (100, 100), (0, 100)])
    cfg = ReferenceMarkConfig(min_distance=10)
    sl = Slice(0, 0.0, [square], origin=(0, 0), mark_manager=ReferenceMarkManager(), config=cfg)
    with caplog.at_level(logging.WARNING):
        ReferenceMarkService.process_slice(sl)

    assert len(sl.ref_marks) == 1
    assert not [r for r in caplog.records if r.levelno == logging.WARNING]
