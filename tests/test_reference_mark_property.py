from typing import cast

import pytest
from hypothesis import assume, given
from hypothesis import strategies as st
from shapely.geometry import Point, Polygon

from layerforge.models.reference_marks import ReferenceMarkCalculator
from layerforge.models.reference_marks.config import ReferenceMarkConfig, require

# Hypothesis can draw coordinates such as 1e-200. A hull edge that short has a
# squared length of 0 in floating point, and GEOS then divides by zero inside
# ``boundary.distance`` (issue #77). Real meshes have no such edges, so the
# strategy rounds to micrometres and any other RuntimeWarning fails the test.
_COORD = st.floats(0, 100).map(lambda v: round(v, 6))


@pytest.mark.filterwarnings("error::RuntimeWarning")
@given(st.lists(st.tuples(_COORD, _COORD), min_size=3, max_size=6))
def test_the_chosen_mark_fits_inside_the_polygon(coords):
    hull = Polygon(coords).convex_hull
    assume(isinstance(hull, Polygon) and hull.area > 0)
    poly = cast(Polygon, hull)
    cfg = ReferenceMarkConfig(min_distance=1).resolved(layer_height=3.0)
    min_distance = require(cfg.min_distance, "min_distance")
    size = require(cfg.size, "size")
    mark = ReferenceMarkCalculator.choose_mark_for_pair(
        poly,
        [poly],
        [],
        [],
        min_distance=min_distance,
        min_web=0,
        tolerance=require(cfg.tolerance, "tolerance"),
        available_shapes=cfg.available_shapes,
        size=size,
        angle=cfg.angle,
    )
    if mark is None:
        return
    pt = Point(mark.x, mark.y)
    assert poly.contains(pt)
    assert poly.boundary.distance(pt) >= min_distance
    # The whole hole fits: a disc of the mark's size lies inside the piece (TR-5).
    assert poly.boundary.distance(pt) >= size / 2
