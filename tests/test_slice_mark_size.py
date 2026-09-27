"""The size of a new mark follows the sheet, not the place (TR-6, #62)."""

import logging

import pytest
from shapely.geometry import box

from layerforge.models.reference_marks import ReferenceMarkConfig
from layerforge.models.reference_marks.pair_marking import plan_marks
from layerforge.models.slicing.slice import Slice

NEAR = box(0, 0, 20, 20)
FAR = box(200, 0, 220, 20)


def _one_new_mark_size(layer_height: float, **config) -> float:
    """The size of the one mark two identical, fully-overlapping layers share."""
    cfg = ReferenceMarkConfig(**config)
    marks = plan_marks([[NEAR], [NEAR]], cfg, layer_height)
    assert len(marks[0]) == 1
    return marks[0][0].size


def test_a_new_mark_has_the_size_of_the_sheet_wherever_it_lies():
    """The old rule gave 3 near the origin and 5 far from it; NEAR and FAR are no longer both
    testable in one call now that marks are chosen per pair, not per polygon of one slice -- see
    the next test, which keeps both pieces and both sizes."""
    cfg = ReferenceMarkConfig()
    marks = plan_marks([[NEAR, FAR], [NEAR, FAR]], cfg, layer_height=3.0)
    assert [m.size for m in marks[0]] == [3.0, 3.0]


@pytest.mark.parametrize(
    ("layer_height", "expected"),
    [
        (3.0, 3.0),  # the sheet term: 1 x thickness
        (5.0, 5.0),
        (0.2, 0.45),  # the kerf term: 1.5 x 0.3
    ],
)
def test_the_default_size_is_the_larger_of_the_sheet_term_and_the_kerf_term(layer_height, expected):
    assert _one_new_mark_size(layer_height) == pytest.approx(expected)


def test_a_configured_size_replaces_the_sheet_rule():
    assert _one_new_mark_size(3.0, size=7.0) == pytest.approx(7.0)


def test_the_slice_resolves_its_config_with_its_layer_height():
    config = Slice(0, 0.0, [NEAR], config=ReferenceMarkConfig(), layer_height=3.0).config
    assert (config.size, config.min_distance) == (3.0, 3.0)
    assert config.tolerance == pytest.approx(0.3)


def test_a_slice_needs_its_layer_height():
    """#165 item 1: without it there is no web and no derived size, so it is required."""
    with pytest.raises(TypeError, match="layer_height"):
        Slice(0, 0.0, [])  # pyright: ignore[reportCallIssue]


def test_a_size_below_the_least_hole_size_warns_once_and_still_runs(caplog):
    """TR-6: the person knows the machine, so it is a warning and not an error."""
    from layerforge.models.loading.mesh import TrimeshMesh
    from layerforge.models.model import Model
    from layerforge.models.slicing.slicer_service import SlicerService

    trimesh = pytest.importorskip("trimesh")
    model = Model(
        TrimeshMesh(trimesh.creation.box(extents=(30, 30, 12))),
        layer_height=3.0,
    )
    with caplog.at_level(logging.WARNING):
        slices = SlicerService.slice_model(model, ReferenceMarkConfig(size=1.0))
    warnings = [r.getMessage() for r in caplog.records if "least hole size" in r.getMessage()]
    assert len(warnings) == 1
    assert "1" in warnings[0] and "3" in warnings[0]
    assert all(m.size == 1.0 for s in slices for m in s.ref_marks)
    assert sum(len(s.ref_marks) for s in slices) > 0


def test_a_default_size_does_not_warn(caplog):
    from layerforge.models.loading.mesh import TrimeshMesh
    from layerforge.models.model import Model
    from layerforge.models.slicing.slicer_service import SlicerService

    trimesh = pytest.importorskip("trimesh")
    model = Model(
        TrimeshMesh(trimesh.creation.box(extents=(30, 30, 12))),
        layer_height=3.0,
    )
    with caplog.at_level(logging.WARNING):
        SlicerService.slice_model(model, ReferenceMarkConfig())
    assert not [r for r in caplog.records if "least hole size" in r.getMessage()]
