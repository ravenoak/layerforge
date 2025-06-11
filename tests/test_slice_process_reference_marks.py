import pytest
pytest.importorskip("shapely")
from shapely.geometry import Polygon

from layerforge.models.reference_marks import (
    ReferenceMarkManager,
    ReferenceMarkConfig,
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
    cfg1 = ReferenceMarkConfig(min_distance=10, angle=45, color="red")
    sl1 = Slice(0, 0.0, [square], origin=(0, 0), mark_manager=manager, config=cfg1)
    ReferenceMarkService.process_slice(sl1)
    assert sl1.ref_marks[0].angle == 45
    assert sl1.ref_marks[0].color == "red"

    cfg2 = ReferenceMarkConfig(min_distance=10, angle=90, color="blue")
    sl2 = Slice(1, 0.0, [square], origin=(0, 0), mark_manager=manager, config=cfg2)
    ReferenceMarkService.process_slice(sl2)
    assert sl2.ref_marks[0].angle == 45
    assert sl2.ref_marks[0].color == "red"
    assert manager.marks[0].angle == 45
    assert manager.marks[0].color == "red"
