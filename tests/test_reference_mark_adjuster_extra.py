from shapely.geometry import Polygon

from layerforge.models.reference_marks import (
    ReferenceMarkAdjuster,
    ReferenceMarkConfig,
    ReferenceMark,
)


def test_overlapping_marks_removed():
    square = Polygon([(0, 0), (50, 0), (50, 50), (0, 50)])
    marks = [
        ReferenceMark(25, 25, "circle", 3),
        ReferenceMark(27, 25, "square", 3),
    ]
    cfg = ReferenceMarkConfig(min_distance=5)
    adjusted = ReferenceMarkAdjuster.adjust_marks(marks, [square], config=cfg)
    assert len(adjusted) == 1
    assert adjusted[0].x == 25 and adjusted[0].y == 25


def test_mark_near_other_polygon_removed():
    poly1 = Polygon([(0, 0), (50, 0), (50, 50), (0, 50)])
    poly2 = Polygon([(50, 0), (100, 0), (100, 50), (50, 50)])
    mark = ReferenceMark(45, 25, "circle", 3)
    cfg = ReferenceMarkConfig(min_distance=10)
    adjusted = ReferenceMarkAdjuster.adjust_marks([mark], [poly1, poly2], config=cfg)
    assert adjusted == []
