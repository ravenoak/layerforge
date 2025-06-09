import pytest
from shapely.geometry import Polygon

import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "reference_mark_adjuster",
    Path(__file__).resolve().parents[1]
    / "layerforge/models/reference_marks/reference_mark_adjuster.py",
)
adjuster = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adjuster)  # type: ignore
ReferenceMarkAdjuster = adjuster.ReferenceMarkAdjuster


def test_centroid_inside_kept():
    square = Polygon([(0, 0), (100, 0), (100, 100), (0, 100)])
    marks = [(50, 50, 'circle', 3)]
    adjusted = ReferenceMarkAdjuster.adjust_marks(marks, [square], min_distance=10)
    assert adjusted == marks


def test_marks_near_boundary_removed():
    square = Polygon([(0, 0), (100, 0), (100, 100), (0, 100)])
    marks = [
        (5, 5, 'circle', 3),    # inside but near boundary
        (105, 50, 'square', 3), # outside near boundary
        (95, 95, 'circle', 3),  # inside near boundary
    ]
    adjusted = ReferenceMarkAdjuster.adjust_marks(marks, [square], min_distance=10)
    assert adjusted == []
