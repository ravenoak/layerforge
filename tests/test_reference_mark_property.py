import random
from typing import cast

import pytest
from hypothesis import assume, given
from hypothesis import strategies as st
from shapely.geometry import Point, Polygon

from layerforge.models.reference_marks import (
    ReferenceMarkCalculator,
    ReferenceMarkConfig,
    ReferenceMarkManager,
)
from layerforge.models.reference_marks.config import require
from layerforge.models.slicing.slice import Slice
from layerforge.utils import calculate_distance

# Hypothesis can draw coordinates such as 1e-200. A hull edge that short has a
# squared length of 0 in floating point, and GEOS then divides by zero inside
# ``boundary.distance`` (issue #77). Real meshes have no such edges, so the
# strategy rounds to micrometres and any other RuntimeWarning fails the test.
_COORD = st.floats(0, 100).map(lambda v: round(v, 6))


@pytest.mark.filterwarnings("error::RuntimeWarning")
@given(st.lists(st.tuples(_COORD, _COORD), min_size=3, max_size=6))
def test_marks_inside_polygon(coords):
    hull = Polygon(coords).convex_hull
    assume(isinstance(hull, Polygon) and hull.area > 0)
    poly = cast(Polygon, hull)
    cfg = ReferenceMarkConfig(min_distance=1)
    manager = ReferenceMarkManager(config=cfg)
    sl = Slice(0, 0.0, [poly], origin=(0, 0), mark_manager=manager, config=cfg, layer_height=3.0)
    marks = ReferenceMarkCalculator.get_stable_marks(sl, [], config=cfg)
    min_distance = require(sl.config.min_distance, "min_distance")
    size = require(sl.config.size, "size")
    for x, y in marks:
        pt = Point(x, y)
        assert poly.contains(pt)
        assert poly.boundary.distance(pt) >= min_distance
        # The whole hole fits: a disc of the mark's size lies inside the piece (TR-5).
        assert poly.boundary.distance(pt) >= size / 2
    for i, m1 in enumerate(marks):
        for m2 in marks[i + 1 :]:
            assert calculate_distance(m1[0], m1[1], m2[0], m2[1]) >= min_distance


def test_stability_score_permutation():
    pts: list[tuple[float, float]] = [(0, 0), (10, 0), (0, 10)]
    score = ReferenceMarkCalculator._stability_score(pts)
    random.shuffle(pts)
    assert score == pytest.approx(ReferenceMarkCalculator._stability_score(pts))
