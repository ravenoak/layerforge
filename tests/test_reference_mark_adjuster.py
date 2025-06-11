import pytest
pytest.importorskip("shapely")
from shapely.geometry import Polygon

from layerforge.models.reference_marks import (
    ReferenceMarkAdjuster,
    ReferenceMarkConfig,
    ReferenceMark,
)


def test_centroid_inside_kept():
    square = Polygon([(0, 0), (100, 0), (100, 100), (0, 100)])
    marks = [ReferenceMark(50, 50, 'circle', 3)]
    config = ReferenceMarkConfig(min_distance=10)
    adjusted = ReferenceMarkAdjuster.adjust_marks(marks, [square], config=config)
    assert adjusted == marks


def test_marks_near_boundary_removed():
    square = Polygon([(0, 0), (100, 0), (100, 100), (0, 100)])
    marks = [
        ReferenceMark(5, 5, 'circle', 3),    # inside but near boundary
        ReferenceMark(105, 50, 'square', 3), # outside near boundary
        ReferenceMark(95, 95, 'circle', 3),  # inside near boundary
    ]
    config = ReferenceMarkConfig(min_distance=10)
    adjusted = ReferenceMarkAdjuster.adjust_marks(marks, [square], config=config)
    assert adjusted == []
