"""_warn_about_unmarked_contours gives the right remedy for the real cause (review of #63).

A contour with no mark either has no neighbouring layer to pair with at all (a single-slice
model: no size or distance change can fix that) or has a neighbour but nothing fit (where the
--mark-min-distance / --mark-size advice is at least sometimes right).
"""

import logging

from shapely.geometry import box

from layerforge.models.reference_marks import ReferenceMarkConfig
from layerforge.models.slicing.slice import Slice

SQUARE = box(0, 0, 10, 10)


def test_a_single_slice_model_gets_the_no_neighbour_message(caplog):
    slice_ = Slice(
        0,
        0.0,
        [SQUARE],
        config=ReferenceMarkConfig(),
        layer_height=3.0,
        ref_marks=[],
        total_slices=1,
    )
    with caplog.at_level(logging.WARNING):
        slice_.adjust_marks()
    messages = [r.getMessage() for r in caplog.records]
    assert len(messages) == 1
    assert "only one layer" in messages[0]
    assert "no neighbouring layer" in messages[0]
    assert "--mark-min-distance" not in messages[0], "no size/distance change fixes this"


def test_a_multi_slice_run_keeps_the_size_and_distance_advice(caplog):
    slice_ = Slice(
        0,
        0.0,
        [SQUARE],
        config=ReferenceMarkConfig(),
        layer_height=3.0,
        ref_marks=[],
        total_slices=3,
    )
    with caplog.at_level(logging.WARNING):
        slice_.adjust_marks()
    messages = [r.getMessage() for r in caplog.records]
    assert len(messages) == 1
    assert "--mark-min-distance" in messages[0] and "--mark-size" in messages[0]
    assert "only one layer" not in messages[0]


def test_an_unknown_total_slices_keeps_the_size_and_distance_advice(caplog):
    """`total_slices=None` (the default) must not be mistaken for the single-slice case."""
    slice_ = Slice(0, 0.0, [SQUARE], config=ReferenceMarkConfig(), layer_height=3.0, ref_marks=[])
    with caplog.at_level(logging.WARNING):
        slice_.adjust_marks()
    messages = [r.getMessage() for r in caplog.records]
    assert len(messages) == 1
    assert "--mark-min-distance" in messages[0]
