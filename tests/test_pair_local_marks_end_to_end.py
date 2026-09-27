"""End-to-end acceptance for #63 (TR-9): the sheared cylinder of #107, and TR-9's core invariant."""

import math

import pytest

pytest.importorskip("trimesh")
pytest.importorskip("shapely")
import trimesh

from layerforge.models.loading.mesh import TrimeshMesh
from layerforge.models.model import Model
from layerforge.models.reference_marks import ReferenceMarkConfig
from layerforge.models.slicing.slicer_service import SlicerService


def test_every_slice_of_the_sheared_cylinder_gets_a_mark(sheared_cylinder_stl):
    """#107's acceptance test: with tolerance and min_distance comparable to the shear, retirement
    (not a stale, drifting mark) keeps every slice covered."""
    model = Model(TrimeshMesh(trimesh.load_mesh(str(sheared_cylinder_stl))), layer_height=3.0)
    slices = SlicerService.slice_model(model, ReferenceMarkConfig(tolerance=25, min_distance=10))
    assert all(len(s.ref_marks) >= 1 for s in slices), (
        f"slices with no mark: {[s.index for s in slices if not s.ref_marks]}"
    )


def test_no_two_distinct_marks_of_the_sheared_cylinder_are_within_tolerance(sheared_cylinder_stl):
    model = Model(TrimeshMesh(trimesh.load_mesh(str(sheared_cylinder_stl))), layer_height=3.0)
    tolerance = 25
    slices = SlicerService.slice_model(
        model, ReferenceMarkConfig(tolerance=tolerance, min_distance=10)
    )
    distinct = []
    for s in slices:
        for m in s.ref_marks:
            if not any(m is d for d in distinct):
                distinct.append(m)
    for i, a in enumerate(distinct):
        for b in distinct[i + 1 :]:
            assert math.hypot(a.x - b.x, a.y - b.y) > tolerance


def test_no_alignment_mark_is_a_hole_in_every_layer_of_a_three_layer_stack():
    """TR-9's core promise. A cone-like stack whose cross-section shrinks steadily forces at
    least one retirement, so no single mark can span all layers."""
    trimesh = pytest.importorskip("trimesh")
    mesh = trimesh.creation.cone(radius=30.0, height=30.0, sections=48)
    model = Model(TrimeshMesh(mesh), layer_height=5.0)
    slices = SlicerService.slice_model(model, ReferenceMarkConfig(min_distance=3))
    assert len(slices) >= 3
    all_marks = [m for s in slices for m in s.ref_marks]
    for mark in all_marks:
        holds_every_slice = all(any(m is mark for m in s.ref_marks) for s in slices)
        assert not holds_every_slice
