import math
from typing import cast

import pytest

pytest.importorskip("trimesh")
pytest.importorskip("shapely")
import trimesh
from shapely.geometry import Point

from layerforge.models.loading.mesh import TrimeshMesh
from layerforge.models.model import Model


def _model(geometry: trimesh.Trimesh) -> Model:
    return Model(TrimeshMesh(geometry), layer_height=5.0)


def _combined(*meshes: trimesh.Trimesh) -> trimesh.Trimesh:
    return cast(trimesh.Trimesh, trimesh.util.concatenate(list(meshes)))


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


def test_tube_slice_is_one_polygon_with_a_hole():
    tube = trimesh.creation.annulus(r_min=5, r_max=10, height=10)
    (contour,) = _model(tube).calculate_slice_contours(0.0)
    assert len(contour.interiors) == 1
    assert not contour.contains(Point(0, 0))
    assert contour.contains(Point(7.5, 0))
    # The ring is about pi * (10^2 - 5^2); the polygon is a slight underestimate.
    assert contour.area == pytest.approx(math.pi * 75, rel=0.05)


def test_nested_tubes_give_two_polygons_with_holes():
    inner = trimesh.creation.annulus(r_min=5, r_max=10, height=10)
    outer = trimesh.creation.annulus(r_min=15, r_max=20, height=10)
    model = _model(_combined(inner, outer))
    contours = model.calculate_slice_contours(0.0)
    assert len(contours) == 2
    assert all(len(c.interiors) == 1 for c in contours)
    # The gap between the two tubes is not part of any polygon.
    assert not any(c.contains(Point(12.5, 0)) for c in contours)


def test_solid_inside_a_hole_is_its_own_polygon():
    tube = trimesh.creation.annulus(r_min=10, r_max=20, height=10)
    rod = trimesh.creation.cylinder(radius=3, height=10)
    contours = _model(_combined(tube, rod)).calculate_slice_contours(0.0)
    assert len(contours) == 2
    assert sorted(len(c.interiors) for c in contours) == [0, 1]
