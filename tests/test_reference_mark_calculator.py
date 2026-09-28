from shapely.geometry import Point, Polygon

from layerforge.models.reference_marks import ReferenceMark, ReferenceMarkCalculator
from layerforge.models.reference_marks.footprint import mark_reach


def test_choose_mark_for_pair_reuses_a_candidate_that_still_fits():
    square = Polygon([(0, 0), (100, 0), (100, 100), (0, 100)])
    candidate = ReferenceMark(x=50, y=50, shape="circle", size=3)
    mark = ReferenceMarkCalculator.choose_mark_for_pair(
        square,
        [square],
        [candidate],
        [],
        min_distance=10,
        min_web=0,
        tolerance=1,
        available_shapes=["circle"],
        size=3,
        angle=0.0,
    )
    assert mark is candidate


def test_choose_mark_for_pair_retires_a_candidate_that_no_longer_fits():
    square = Polygon([(0, 0), (100, 0), (100, 100), (0, 100)])
    # 5 from the edge: closer than min_distance, so this candidate cannot be reused.
    candidate = ReferenceMark(x=5, y=50, shape="circle", size=3)
    mark = ReferenceMarkCalculator.choose_mark_for_pair(
        square,
        [square],
        [candidate],
        [],
        min_distance=10,
        min_web=0,
        tolerance=1,
        available_shapes=["circle"],
        size=3,
        angle=0.0,
    )
    assert mark is not None
    assert mark is not candidate
    assert Point(mark.x, mark.y).distance(square.boundary) >= 10


def test_choose_mark_for_pair_picks_the_shape_before_the_point():
    """#198: the disc must match the chosen shape's own reach, not the largest in the list."""
    square = Polygon([(0, 0), (100, 0), (100, 100), (0, 100)])
    mark = ReferenceMarkCalculator.choose_mark_for_pair(
        square,
        [square],
        [],
        [],
        min_distance=1,
        min_web=0,
        tolerance=1,
        available_shapes=["circle", "triangle"],
        size=3,
        angle=0.0,
    )
    assert mark is not None
    assert mark.shape == "triangle"  # least symmetry order wins (choose_shape, #61)


def test_choose_mark_for_pair_avoids_a_mark_from_the_other_pairing():
    square = Polygon([(0, 0), (100, 0), (100, 100), (0, 100)])
    other_pairing_mark = ReferenceMark(x=50, y=50, shape="circle", size=3)
    mark = ReferenceMarkCalculator.choose_mark_for_pair(
        square,
        [square],
        [],
        [other_pairing_mark],
        min_distance=1,
        min_web=0,
        tolerance=1,
        available_shapes=["circle"],
        size=3,
        angle=0.0,
    )
    # This fixture's gap is 2 * mark_reach("circle", 3) (~3.0, not the 1 this test used to
    # assert): a vacuous `mark is None or ...` used to pass even if the function always
    # returned None, so this now requires a mark and checks the real bound.
    assert mark is not None
    gap = 2 * mark_reach("circle", 3)
    assert Point(mark.x, mark.y).distance(Point(50, 50)) >= gap


def test_choose_mark_for_pair_returns_none_when_nothing_fits():
    tiny = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
    mark = ReferenceMarkCalculator.choose_mark_for_pair(
        tiny,
        [tiny],
        [],
        [],
        min_distance=10,
        min_web=0,
        tolerance=1,
        available_shapes=["circle"],
        size=3,
        angle=0.0,
    )
    assert mark is None
