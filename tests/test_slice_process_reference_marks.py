from shapely.geometry import Polygon

from layerforge.models.reference_marks import ReferenceMarkManager, ReferenceMarkConfig
from layerforge.models.slicing.slice import Slice


def test_new_mark_added_to_manager():
    square = Polygon([(0, 0), (100, 0), (100, 100), (0, 100)])
    manager = ReferenceMarkManager()
    cfg = ReferenceMarkConfig(min_distance=10)
    sl = Slice(0, 0.0, [square], origin=(0, 0), mark_manager=manager, config=cfg)
    sl.process_reference_marks()
    assert len(sl.ref_marks) == 1
    # manager should now contain the new mark
    assert len(manager.marks) == 1
    assert manager.marks[0].x == sl.ref_marks[0].x
    assert manager.marks[0].y == sl.ref_marks[0].y
