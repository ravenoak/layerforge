"""Shapes are chosen by need, not by list order (TR-8, #61).

Every mark of a run has one angle. A shape with a direction (symmetry order 1) then fixes the
rotation of a piece with one mark, and a circle or a square cannot. So the tool prefers a shape
with a direction, and the order of `--available-shapes` no longer matters.
"""

import itertools
import math

import pytest
from hypothesis import given
from hypothesis import strategies as st
from shapely.geometry import box

from layerforge.models.reference_marks import (
    ReferenceMark,
    ReferenceMarkConfig,
    ReferenceMarkManager,
    ReferenceMarkService,
    rotation_symmetry,
)
from layerforge.models.reference_marks.shape_choice import choose_shape
from layerforge.models.slicing.slice import Slice

DEFAULTS = ["circle", "square", "triangle", "arrow"]


@pytest.mark.parametrize("order", list(itertools.permutations(DEFAULTS)))
def test_the_defaults_give_the_triangle_in_any_order(order):
    assert choose_shape(order) == "triangle"


@pytest.mark.parametrize(
    ("available", "expected"),
    [
        (["arrow", "triangle"], "triangle"),
        (["triangle", "arrow"], "triangle"),
        (["arrow"], "arrow"),
        (["circle", "arrow"], "arrow"),
        (["square", "arrow", "circle"], "arrow"),
        (["circle", "square"], "square"),
        (["square", "circle"], "square"),
        (["circle"], "circle"),
        (["square"], "square"),
        (["triangle", "triangle"], "triangle"),
    ],
)
def test_the_choice_does_not_depend_on_the_order_of_the_list(available, expected):
    assert choose_shape(available) == expected


def test_an_empty_list_is_refused():
    with pytest.raises(ValueError, match="at least one shape"):
        choose_shape([])


def test_an_unknown_shape_is_refused():
    with pytest.raises(ValueError, match="hexagon"):
        choose_shape(["hexagon"])


DIRECTIONAL = st.lists(st.sampled_from(["triangle", "arrow"]), min_size=1, max_size=2)
OTHERS = st.lists(st.sampled_from(["circle", "square"]), max_size=2)


@given(
    DIRECTIONAL,
    OTHERS,
    st.integers(0, 7),
    st.lists(
        st.tuples(st.integers(-20, 20), st.integers(-20, 20)), min_size=1, max_size=5, unique=True
    ),
)
def test_marks_of_the_chosen_shape_at_one_angle_can_be_stacked_one_way_only(
    directional, others, angle_step, points
):
    """TR-2 holds by construction when a shape with a direction is available."""
    shape = choose_shape([*others, *directional])
    marks = [
        ReferenceMark(x=x, y=y, shape=shape, size=3.0, angle=angle_step * math.pi / 4)
        for x, y in points
    ]
    assert not rotation_symmetry(marks, tolerance=1e-6).has_nonidentity


def _slice(contours, layer_height=3.0, manager=None, **config) -> Slice:
    cfg = ReferenceMarkConfig(**config)
    manager = manager or ReferenceMarkManager(config=cfg.resolved(layer_height))
    return Slice(0, 0.0, contours, mark_manager=manager, config=cfg, layer_height=layer_height)


@pytest.mark.parametrize("shapes", [["arrow", "triangle"], ["triangle", "arrow"]])
def test_a_slice_marks_with_the_shape_of_greatest_need_whatever_the_list_order(shapes):
    layer = _slice([box(0, 0, 20, 20)], available_shapes=shapes)
    ReferenceMarkService.process_slice(layer)
    assert [m.shape for m in layer.ref_marks] == ["triangle"]


def test_two_pieces_of_one_slice_get_the_same_directional_shape():
    layer = _slice([box(0, 0, 20, 20), box(100, 0, 120, 20)])
    ReferenceMarkService.process_slice(layer)
    assert [m.shape for m in layer.ref_marks] == ["triangle", "triangle"]


def test_a_stored_mark_keeps_its_shape_when_the_list_changes():
    manager = ReferenceMarkManager()
    first = _slice([box(0, 0, 20, 20)], manager=manager, available_shapes=["circle"])
    ReferenceMarkService.process_slice(first)
    second = _slice([box(0, 0, 20, 20)], manager=manager, available_shapes=["arrow", "triangle"])
    ReferenceMarkService.process_slice(second)
    assert [m.shape for m in first.ref_marks] == ["circle"]
    assert [m.shape for m in second.ref_marks] == ["circle"]


def test_every_slice_of_a_cube_at_the_defaults_has_marks_that_fix_the_rotation():
    """The 20 mm cube of the getting-started page: one mark per slice, and TR-2 holds."""
    from layerforge.models.loading.mesh import TrimeshMesh
    from layerforge.models.model import Model
    from layerforge.models.slicing.slicer_service import SlicerService

    trimesh = pytest.importorskip("trimesh")
    model = Model(TrimeshMesh(trimesh.creation.box(extents=(20, 20, 20))), layer_height=5.0)
    slices = SlicerService.slice_model(model, ReferenceMarkConfig())
    assert len(slices) == 4
    for layer in slices:
        assert [m.shape for m in layer.ref_marks] == ["triangle"]
        assert not rotation_symmetry(layer.ref_marks, tolerance=1e-6).has_nonidentity
