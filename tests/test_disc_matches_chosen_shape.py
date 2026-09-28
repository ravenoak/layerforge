"""#198: the calculator's disc must match the chosen shape's own reach, not the largest listed.

The four rows below reproduce the issue's own table (a 10 mm cube at layer height 5, and
6.000 / 6.003 / 6.004 mm square boxes at layer height 3), with two corrections made after
measuring the current, pair-driven algorithm (see the PR text for the full explanation):

- The 6 mm rows use a square footprint 9 mm tall (three whole 3 mm layers, matching the
  issue's own "(3 slices)" note), not a 6 x 20 x 3 mm plate: a plate exactly one layer_height
  thick has only one slice and so no adjacent pair at all, and ``plan_marks`` never places a
  mark without one.
- The default-list and triangle-only counts for the 10 mm cube and the 6.000 mm box are 0, not
  2: both are cut exactly at the point where ``min_distance`` equals half the piece's own
  width, and the pair's shrunk region (``overlap.buffer(-min_distance)``) collapses to an empty
  polygon at that exact value, before any shape or disc is even considered. That is a property
  of shapely's erosion at the critical radius, not of #198's disc-sizing bug; both those rows
  give the same (0) count for the default list and for triangle alone, so they still support
  the issue's acceptance criterion. The 6.003 and 6.004 mm rows are the ones that actually
  exercise the fix: their half-width clears ``min_distance`` by just enough for the triangle's
  own reach (radius + web margin) but not, before this fix, for the circle's.
"""

import pytest

pytest.importorskip("trimesh")
pytest.importorskip("shapely")

import trimesh

from layerforge.models.loading.mesh import TrimeshMesh
from layerforge.models.model import Model
from layerforge.models.reference_marks import ReferenceMarkConfig
from layerforge.models.slicing.slicer_service import SlicerService


def _mark_counts(extents, layer_height, **config) -> list[int]:
    mesh = trimesh.creation.box(extents=extents)
    model = Model(TrimeshMesh(mesh), layer_height=layer_height)
    slices = SlicerService.slice_model(model, ReferenceMarkConfig(**config))
    return [len(s.ref_marks) for s in slices]


@pytest.mark.parametrize(
    ("extents", "layer_height", "default_list_marked", "triangle_only_marked"),
    [
        ((10, 10, 10), 5, 0, 0),
        ((6.000, 6.000, 9), 3, 0, 0),
        ((6.003, 6.003, 9), 3, 3, 3),
        ((6.004, 6.004, 9), 3, 3, 3),
    ],
)
def test_the_default_list_and_triangle_alone_agree(
    extents, layer_height, default_list_marked, triangle_only_marked
):
    default_counts = _mark_counts(extents, layer_height)
    triangle_counts = _mark_counts(extents, layer_height, available_shapes=["triangle"])
    assert sum(1 for n in default_counts if n > 0) == default_list_marked
    assert sum(1 for n in triangle_counts if n > 0) == triangle_only_marked
