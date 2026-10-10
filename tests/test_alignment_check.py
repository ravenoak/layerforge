"""check_alignment: adjacent pieces share a mark and no turn maps the shared marks onto themselves.

TR-2 and TR-12 (#92). The slices are built by hand, so each case states the marks it holds.
"""

import pytest
from shapely.geometry import Point, Polygon, box

from layerforge.models.reference_marks import ReferenceMark, ReferenceMarkConfig
from layerforge.models.slicing.alignment_check import AlignmentFailure, check_alignment
from layerforge.models.slicing.slice import Slice

LAYER_HEIGHT = 3.0
SQUARE = box(0, 0, 20, 20)


def _slice(index, contours, marks, tolerance=None):
    config = ReferenceMarkConfig(tolerance=tolerance)
    return Slice(index, float(index), contours, config, layer_height=LAYER_HEIGHT, ref_marks=marks)


def _mark(shape, x=10.0, y=10.0):
    return ReferenceMark(x=x, y=y, shape=shape, size=3.0)


def _ids(failures):
    """The pieces and the reason of each failure, without the place."""
    return [
        (f.lower_slice, f.lower_piece, f.upper_slice, f.upper_piece, f.reason) for f in failures
    ]


def test_a_pair_that_shares_one_triangle_passes():
    mark = _mark("triangle")
    assert check_alignment([_slice(0, [SQUARE], [mark]), _slice(1, [SQUARE], [mark])]) == []


@pytest.mark.parametrize("shape", ["circle", "square"])
def test_a_pair_that_shares_one_circle_or_square_does_not_fix_the_rotation(shape):
    mark = _mark(shape)
    failures = check_alignment([_slice(0, [SQUARE], [mark]), _slice(1, [SQUARE], [mark])])
    assert _ids(failures) == [(0, 0, 1, 0, "rotation_not_fixed")]


def test_a_pair_with_no_marks_shares_no_mark_and_is_not_read_as_unlimited_symmetry():
    failures = check_alignment([_slice(0, [SQUARE], []), _slice(1, [SQUARE], [])])
    assert _ids(failures) == [(0, 0, 1, 0, "no_shared_mark")]


def test_a_mark_in_only_one_slice_is_not_shared():
    mark = _mark("triangle")
    failures = check_alignment([_slice(0, [SQUARE], [mark]), _slice(1, [SQUARE], [])])
    assert [f.reason for f in failures] == ["no_shared_mark"]


def test_a_mark_outside_the_upper_piece_is_not_shared():
    mark = _mark("triangle", x=5.0, y=5.0)
    upper = box(10, 10, 30, 30)  # overlaps SQUARE, but (5, 5) is not inside it
    failures = check_alignment([_slice(0, [SQUARE], [mark]), _slice(1, [upper], [mark])])
    assert [f.reason for f in failures] == ["no_shared_mark"]


def test_one_slice_and_no_slices_pass():
    assert check_alignment([_slice(0, [SQUARE], [])]) == []
    assert check_alignment([]) == []


def test_a_mark_tolerance_of_zero_does_not_raise():
    mark = _mark("circle")
    slices = [
        _slice(0, [SQUARE], [mark], tolerance=0.0),
        _slice(1, [SQUARE], [mark], tolerance=0.0),
    ]
    assert [f.reason for f in check_alignment(slices)] == ["rotation_not_fixed"]


def test_each_pair_of_a_split_is_checked_on_its_own():
    left, right = box(0, 0, 10, 20), box(12, 0, 22, 20)
    mark = _mark("triangle", x=5.0, y=10.0)  # inside the left piece only
    lower = _slice(0, [box(0, 0, 22, 20)], [mark])
    upper = _slice(1, [left, right], [mark])
    assert _ids(check_alignment([lower, upper])) == [(0, 0, 1, 1, "no_shared_mark")]


def test_a_piece_that_overlaps_nothing_has_no_pair_and_passes():
    mark = _mark("triangle")
    far = box(100, 100, 110, 110)
    assert check_alignment([_slice(0, [SQUARE], [mark]), _slice(1, [SQUARE, far], [mark])]) == []


def test_pieces_that_overlap_by_less_than_the_threshold_are_not_a_pair():
    """TR-9: `plan_marks` does not mark such a pair, so the check does not ask for a mark."""
    config = ReferenceMarkConfig(min_overlap_area=1e9)
    lower = Slice(0, 0.0, [SQUARE], config, layer_height=LAYER_HEIGHT)
    upper = Slice(1, 1.0, [SQUARE], config, layer_height=LAYER_HEIGHT)
    assert check_alignment([lower, upper]) == []


def test_the_messages_name_both_pieces_the_place_and_the_remedy():
    where = "slices 3 and 4 (pieces 0 and 2, at x 5, y -1.5 in the model): "
    none = AlignmentFailure(3, 0, 4, 2, 5.0, -1.5, "no_shared_mark").message()
    assert none.startswith(where)
    assert "--mark-min-distance" in none and "--mark-size" in none
    turn = AlignmentFailure(3, 0, 4, 2, 5.0, -1.5, "rotation_not_fixed").message()
    assert turn.startswith(where)
    assert "--available-shapes" in turn


@pytest.mark.parametrize(
    ("x", "y", "shown"),
    [
        (-1e-17, -0.0, "at x 0, y 0 in the model"),  # float noise and negative zero read as 0
        (3.14159265, -1.5, "at x 3.142, y -1.5 in the model"),  # three decimals
        (1234.5, 0.0004, "at x 1234.5, y 0 in the model"),
    ],
)
def test_the_place_is_rounded_to_three_decimals_without_exponents_or_negative_zero(x, y, shown):
    assert shown in AlignmentFailure(0, 0, 1, 0, x, y, "no_shared_mark").message()


def test_a_failure_names_a_point_inside_both_pieces_even_when_the_centroid_is_in_a_hole():
    # The centroid of a ring is (20, 20), in the hole: it is not on either piece.
    ring = Polygon(box(0, 0, 40, 40).exterior.coords, [box(10, 10, 30, 30).exterior.coords])
    failures = check_alignment([_slice(0, [ring], []), _slice(1, [ring], [])])
    assert len(failures) == 1
    point = Point(failures[0].x, failures[0].y)
    assert ring.contains(point)


def test_the_place_is_where_the_two_pieces_overlap():
    left, right = box(0, 0, 10, 10), box(100, 100, 120, 120)
    upper = box(5, 5, 15, 15)  # overlaps `left` in (5, 5)-(10, 10) and `right` not at all
    failures = check_alignment([_slice(0, [left, right], []), _slice(1, [upper], [])])
    assert len(failures) == 1
    assert left.contains(Point(failures[0].x, failures[0].y))
    assert upper.contains(Point(failures[0].x, failures[0].y))
