"""The size of a new mark follows the sheet, not the place (TR-6, #62)."""

import logging

import pytest
from shapely.geometry import box

from layerforge.models.reference_marks import (
    ReferenceMarkConfig,
    ReferenceMarkManager,
    ReferenceMarkService,
)
from layerforge.models.slicing.slice import Slice


def _slice(contours, layer_height, **config) -> Slice:
    cfg = ReferenceMarkConfig(**config)
    manager = ReferenceMarkManager(config=cfg.resolved(layer_height))
    return Slice(0, 0.0, contours, mark_manager=manager, config=cfg, layer_height=layer_height)


NEAR = box(0, 0, 20, 20)
FAR = box(200, 0, 220, 20)


def test_a_new_mark_has_the_size_of_the_sheet_wherever_it_lies():
    """The old rule gave 3 near the origin and 5 far from it."""
    layer = _slice([NEAR, FAR], layer_height=3.0)
    ReferenceMarkService.process_slice(layer)
    assert [m.size for m in layer.ref_marks] == [3.0, 3.0]


@pytest.mark.parametrize(
    ("layer_height", "expected"),
    [
        (3.0, 3.0),  # the sheet term: 1 x thickness
        (5.0, 5.0),
        (0.2, 0.45),  # the kerf term: 1.5 x 0.3
    ],
)
def test_the_default_size_is_the_larger_of_the_sheet_term_and_the_kerf_term(layer_height, expected):
    layer = _slice([NEAR], layer_height=layer_height)
    ReferenceMarkService.process_slice(layer)
    assert [m.size for m in layer.ref_marks] == [pytest.approx(expected)]


def test_a_configured_size_replaces_the_sheet_rule():
    layer = _slice([NEAR, FAR], layer_height=3.0, size=7.0)
    ReferenceMarkService.process_slice(layer)
    assert [m.size for m in layer.ref_marks] == [7.0, 7.0]


def test_the_slice_resolves_its_config_with_its_layer_height():
    config = _slice([NEAR], layer_height=3.0).config
    assert (config.size, config.min_distance) == (3.0, 3.0)
    assert config.tolerance == pytest.approx(0.3)


def test_a_slice_needs_its_layer_height():
    """#165 item 1: without it there is no web and no derived size, so it is required."""
    with pytest.raises(TypeError, match="layer_height"):
        Slice(  # pyright: ignore[reportCallIssue]
            0, 0.0, [], mark_manager=ReferenceMarkManager()
        )


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
