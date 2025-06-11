import random

import pytest
from hypothesis import given, strategies as st, assume
from shapely.geometry import Polygon, Point

from layerforge.models.reference_marks import (
    ReferenceMarkCalculator,
    ReferenceMarkManager,
    ReferenceMarkConfig,
)
from layerforge.models.slicing.slice import Slice
from layerforge.utils import calculate_distance


@given(st.lists(st.tuples(st.floats(0, 100), st.floats(0, 100)), min_size=3, max_size=6))
def test_marks_inside_polygon(coords):
    poly = Polygon(coords).convex_hull
    assume(poly.area > 0)
    cfg = ReferenceMarkConfig(min_distance=1)
    manager = ReferenceMarkManager(config=cfg)
    sl = Slice(0, 0.0, [poly], origin=(0, 0), mark_manager=manager, config=cfg)
    marks = ReferenceMarkCalculator.get_stable_marks(sl, [], config=cfg)
    for x, y in marks:
        pt = Point(x, y)
        assert poly.contains(pt)
        assert poly.boundary.distance(pt) >= cfg.min_distance
    for i, m1 in enumerate(marks):
        for m2 in marks[i+1:]:
            assert calculate_distance(m1[0], m1[1], m2[0], m2[1]) >= cfg.min_distance


def test_stability_score_permutation():
    pts = [(0, 0), (10, 0), (0, 10)]
    score = ReferenceMarkCalculator._stability_score(pts)
    random.shuffle(pts)
    assert score == pytest.approx(ReferenceMarkCalculator._stability_score(pts))

