import math

import pytest

pytest.importorskip("trimesh")
pytest.importorskip("shapely")
import trimesh

from layerforge.models.loading.mesh import TrimeshMesh
from layerforge.models.model import Model


def _model(geometry: trimesh.Trimesh) -> Model:
    return Model(TrimeshMesh(geometry), layer_height=5.0, origin=(0.0, 0.0))


def _section_xy_bounds(geometry: trimesh.Trimesh, z: float) -> tuple[float, float, float, float]:
    section = geometry.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
    assert section is not None
    (x0, y0, _), (x1, y1, _) = section.bounds
    return x0, y0, x1, y1


def test_contours_are_in_model_coordinates():
    """A box moved away from the origin keeps its position in every slice."""
    box = trimesh.creation.box(extents=(20, 20, 20))
    box.apply_translation((100, 50, 10))
    model = _model(box)
    for z in (2.5, 10, 17.5):
        (contour,) = model.calculate_slice_contours(z)
        assert contour.bounds == pytest.approx((90, 40, 110, 60))


def test_slices_of_a_tilted_mesh_share_one_frame():
    """The centre of a tilted box moves with height, and the contours follow it."""
    box = trimesh.creation.box(extents=(20, 20, 40))
    box.apply_transform(trimesh.transformations.rotation_matrix(math.radians(30), [0, 1, 0]))
    box.apply_translation((0, 0, -box.bounds[0][2]))
    model = _model(box)

    centres = []
    for z in (15, 20, 30):
        (contour,) = model.calculate_slice_contours(z)
        assert contour.bounds == pytest.approx(_section_xy_bounds(box, z), abs=1e-6)
        centres.append(contour.centroid.x)
    assert centres[0] < centres[1] < centres[2]


def test_plane_that_misses_the_mesh_gives_no_contours():
    box = trimesh.creation.box(extents=(20, 20, 20))
    assert _model(box).calculate_slice_contours(50.0) == []
