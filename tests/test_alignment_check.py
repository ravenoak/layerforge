"""check_alignment: adjacent pieces share a mark and no turn maps the shared marks onto themselves.

TR-2 and TR-12 (#92). The slices are built by hand, so each case states the marks it holds.
"""

import pytest
from shapely.geometry import box

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


def test_a_pair_that_shares_one_triangle_passes():
    mark = _mark("triangle")
    assert check_alignment([_slice(0, [SQUARE], [mark]), _slice(1, [SQUARE], [mark])]) == []


@pytest.mark.parametrize("shape", ["circle", "square"])
def test_a_pair_that_shares_one_circle_or_square_does_not_fix_the_rotation(shape):
    mark = _mark(shape)
    failures = check_alignment([_slice(0, [SQUARE], [mark]), _slice(1, [SQUARE], [mark])])
    assert failures == [AlignmentFailure(0, 0, 1, 0, "rotation_not_fixed")]


def test_a_pair_with_no_marks_shares_no_mark_and_is_not_read_as_unlimited_symmetry():
    failures = check_alignment([_slice(0, [SQUARE], []), _slice(1, [SQUARE], [])])
    assert failures == [AlignmentFailure(0, 0, 1, 0, "no_shared_mark")]


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
    assert check_alignment([lower, upper]) == [AlignmentFailure(0, 0, 1, 1, "no_shared_mark")]


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


def test_the_messages_name_both_pieces_and_the_remedy():
    none = AlignmentFailure(3, 0, 4, 2, "no_shared_mark").message()
    assert none.startswith("slices 3 and 4 (piece 0 and piece 2): ")
    assert "--mark-min-distance" in none and "--mark-size" in none
    turn = AlignmentFailure(3, 0, 4, 2, "rotation_not_fixed").message()
    assert turn.startswith("slices 3 and 4 (piece 0 and piece 2): ")
    assert "--available-shapes" in turn
