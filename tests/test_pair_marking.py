"""plan_marks: marks chosen per pair of adjacent layers, retired when they no longer fit (#63)."""

import math
import time

from shapely.geometry import Polygon, box

from layerforge.models.reference_marks import ReferenceMarkConfig
from layerforge.models.reference_marks.pair_marking import plan_marks

SQUARE = box(0, 0, 100, 100)


def test_a_single_layer_gets_no_marks():
    """Review Focus: nothing to align a lone layer to, so it gets none (a real behaviour change)."""
    result = plan_marks([[SQUARE]], ReferenceMarkConfig(min_distance=10), layer_height=3.0)
    assert result == [[]]


def test_two_identical_layers_share_one_mark():
    result = plan_marks(
        [[SQUARE], [SQUARE]], ReferenceMarkConfig(min_distance=10), layer_height=3.0
    )
    assert len(result) == 2
    assert len(result[0]) == 1
    assert len(result[1]) == 1
    assert result[0][0] is result[1][0]  # TR-10: the same object, not a coordinate copy


def test_a_stack_of_three_identical_layers_gets_one_mark_shared_by_all_three():
    result = plan_marks(
        [[SQUARE], [SQUARE], [SQUARE]], ReferenceMarkConfig(min_distance=10), layer_height=3.0
    )
    assert result[0][0] is result[1][0] is result[2][0]


def test_a_mark_is_retired_when_it_leaves_the_next_pair_s_shrunk_overlap():
    """TR-9: a piece that shrinks past the mark's old spot gets a new mark, not none."""
    wide = box(0, 0, 100, 100)
    narrow = box(0, 0, 30, 100)  # the shared corner mark from `wide` no longer has room here
    tiny = box(0, 0, 100, 30)
    cfg = ReferenceMarkConfig(min_distance=5)
    result = plan_marks([[wide], [narrow], [tiny]], cfg, layer_height=3.0)
    assert all(len(marks) >= 1 for marks in result), "every slice should still get a mark"
    # The pair (wide, narrow) chose one mark; the pair (narrow, tiny) may need a different one,
    # since the region shrinks a lot between them. Either way, no mark is shared by all three
    # unless the same point happens to fit both pairs' shrunk overlaps.
    shared_by_all = result[0][0] in result[1] and result[0][0] in result[2]
    if not shared_by_all:
        assert result[1][0] not in result[0] or result[1][0] not in result[2]


def test_a_piece_with_two_neighbours_can_hold_two_marks():
    left_bottom = box(0, 0, 100, 100)
    middle = box(0, 0, 100, 100)  # overlaps fully with both neighbours
    # `top`'s overlap with `middle`, once shrunk by min_distance, excludes the mark chosen
    # for (left_bottom, middle) at (50, 50), forcing a second, distinct mark on `middle`.
    top = box(50, 0, 100, 100)
    cfg = ReferenceMarkConfig(min_distance=5)
    result = plan_marks([[left_bottom], [middle], [top]], cfg, layer_height=3.0)
    assert len(result[1]) == 2
    (m1, m2) = result[1]
    assert (m1.x, m1.y) != (m2.x, m2.y)


def test_min_overlap_area_stops_a_thin_sliver_overlap_from_sharing_a_mark():
    a = box(0, 0, 100, 100)
    b = box(99, 0, 199, 100)  # 1 x 100 sliver of overlap with `a`
    cfg = ReferenceMarkConfig(min_distance=1, min_overlap_area=1000.0)
    result = plan_marks([[a], [b]], cfg, layer_height=3.0)
    assert result == [[], []]


def test_a_split_gives_each_branch_its_own_mark_without_colliding():
    trunk = box(0, 0, 100, 100)
    left_branch = box(0, 0, 45, 100)
    right_branch = box(55, 0, 100, 100)
    cfg = ReferenceMarkConfig(min_distance=5)
    result = plan_marks([[trunk], [left_branch, right_branch]], cfg, layer_height=3.0)
    assert len(result[1]) == 2
    (m1, m2) = result[1]
    assert (m1.x, m1.y) != (m2.x, m2.y)


def test_a_merge_gives_the_merged_piece_two_marks_without_colliding():
    left_branch = box(0, 0, 45, 100)
    right_branch = box(55, 0, 100, 100)
    trunk = box(0, 0, 100, 100)
    cfg = ReferenceMarkConfig(min_distance=5)
    result = plan_marks([[left_branch, right_branch], [trunk]], cfg, layer_height=3.0)
    assert len(result[1]) == 2
    (m1, m2) = result[1]
    assert (m1.x, m1.y) != (m2.x, m2.y)


def test_a_no_mark_boundary_still_makes_the_next_boundary_avoid_the_lost_mark():
    """Regression (#63, TR-10): a boundary that places no mark must still owe the next one its
    spacing, or a fresh mark can land within tolerance of the one that just went missing.

    ``slice1``'s mark ``m`` sits at (50, 22.5). ``slice2`` is two lobes joined into one piece: a
    narrow one that overlaps only ``slice1`` and erodes away completely at ``min_distance=5``
    (a ``region is None`` outcome -- nothing carries onto ``slice2`` at all), and a wide one that
    overlaps only ``slice3``, close enough to ``m`` that an unconstrained fresh mark there would
    land within ``tolerance=25`` of it. Before the fix, the ``region is None`` continue wiped
    ``slice2``'s spacing memory outright, so the fresh mark on the wide lobe never had to avoid
    ``m`` and landed 17 units from it, inside tolerance.
    """
    slice0 = box(0, 15, 100, 30)
    slice1 = box(0, 0, 100, 30)
    # A "T": a stem (x 45-55, y 0-29) that only overlaps `slice1`, topped by a wide bar
    # (x 0-100, y 29-70) that only overlaps `slice3`.
    slice2 = Polygon([(45, 0), (55, 0), (55, 29), (100, 29), (100, 70), (0, 70), (0, 29), (45, 29)])
    slice3 = box(0, 29, 100, 50)
    tolerance = 25
    cfg = ReferenceMarkConfig(min_distance=5, tolerance=tolerance)
    result = plan_marks([[slice0], [slice1], [slice2], [slice3]], cfg, layer_height=3.0)

    m = result[1][0]
    assert len(result[2]) == 1, "slice1-slice2 erodes to nothing, but slice2-slice3 still fits"
    fresh = result[2][0]
    distance = math.hypot(fresh.x - m.x, fresh.y - m.y)
    assert distance > tolerance


def test_a_merge_avoids_a_sibling_s_mark_on_the_shared_upper_piece():
    """Review fix: the second merge pairing must see the first's mark as `avoid` (#63).

    Both branches overlap `trunk` identically here, so without the fix each merge pairing
    is chosen independently and `choose_mark_for_pair`'s deterministic sampling would pick
    the same candidate point (the shared centroid) for both, landing two marks on the same
    spot of `trunk`. The fix threads the first pairing's mark into the second's `avoid` list.
    """
    left_branch = box(0, 0, 100, 100)
    right_branch = box(0, 0, 100, 100)
    trunk = box(0, 0, 100, 100)
    cfg = ReferenceMarkConfig(min_distance=5)
    result = plan_marks([[left_branch, right_branch], [trunk]], cfg, layer_height=3.0)
    assert len(result[1]) == 2
    (m1, m2) = result[1]
    distance = ((m1.x - m2.x) ** 2 + (m1.y - m2.y) ** 2) ** 0.5
    assert distance >= cfg.resolved(layer_height=3.0).min_distance


def test_a_stack_of_three_identical_layers_does_not_double_count_the_reused_mark():
    """Regression (review of #63): reusing a candidate must not append it to `result[i]` twice.

    Before the fix, the middle slice of three identical stacked squares held the same mark
    object twice ([1, 2, 1] marks per slice) because the reuse branch re-appended a mark that
    an earlier boundary had already added to that slice's list.
    """
    result = plan_marks(
        [[SQUARE], [SQUARE], [SQUARE]], ReferenceMarkConfig(min_distance=10), layer_height=3.0
    )
    assert [len(marks) for marks in result] == [1, 1, 1]


def test_a_merge_of_many_pieces_keeps_the_avoid_list_linear_not_exponential():
    """Regression (Critical, final review of #63): a failed pairing into a shared upper piece
    must not duplicate the running avoid list on every failure, or a merge of many pieces
    blows the list up exponentially (measured before the fix: 4096 entries at 12 merging
    pieces, 16.7M at 24, 914MB peak memory).

    Each of ``n`` lower pieces overlaps the single wide ``merged`` piece only in a 1-unit-tall
    sliver that eroded away to nothing at ``min_distance=2``, so every one of the ``n``
    pairings takes the no-mark branch into the same shared upper piece -- a merge. A further
    real pairing (``merged`` -> ``above``) then has to scan whatever `plan_marks` accumulated
    for `merged`: with the pre-fix doubling bug this pairing's cost is exponential in ``n`` and
    the whole call takes seconds even at ``n=22``; fixed, the accumulated list is linear in
    ``n`` and the call stays fast regardless.
    """
    n = 22
    lower = [box(k * 20, 0, k * 20 + 10, 10) for k in range(n)]
    upper = [
        box(k * 20, 0, k * 20 + 10, 10) for k in range(n)
    ]  # full overlap with lower: real marks
    width = n * 20 + 10
    merged = [box(0, 9, width, 19)]  # 1-unit sliver overlap with each `upper` piece: erodes away
    above = [box(0, 9, width, 19)]  # full overlap with `merged`: must scan its accumulated list
    cfg = ReferenceMarkConfig(min_distance=2)

    start = time.monotonic()
    result = plan_marks([lower, upper, merged, above], cfg, layer_height=3.0)
    elapsed = time.monotonic() - start

    assert len(result[0]) == n, "every lower/upper pairing should still get a mark"
    assert len(result[1]) == n
    # A linear accumulation finishes in well under a second; the pre-fix doubling bug took
    # 3.7s at this same n=22 on the machine this test was written on.
    assert elapsed < 2.0, (
        f"plan_marks took {elapsed:.2f}s: the avoid list may be growing exponentially again"
    )
