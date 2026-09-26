"""The shape contract of TR-7: closed outline, anchored at the centre, size is the
diameter of the smallest circle around the anchor, angle 0 along +x, counter-clockwise."""

import math

import pytest
import svgwrite
import svgwrite.shapes
from hypothesis import given
from hypothesis import strategies as st
from shapely import affinity
from shapely.geometry import Polygon

from layerforge.domain.shapes import Arrow, Circle, Square, Triangle
from layerforge.domain.shapes.base_shape import BaseShape
from layerforge.svg.drawing.strategy_context import StrategyContext
from layerforge.utils.shape_strategies import register_shape_strategies

POLYGON_SHAPES = [Square, Triangle, Arrow]
ALL_SHAPES = [Circle, Square, Triangle, Arrow]


def _drawn(shape: BaseShape) -> list:
    ctx = StrategyContext()
    register_shape_strategies(ctx)
    dwg = svgwrite.Drawing()
    ctx.draw(dwg, shape)
    return [el for el in dwg.elements if el.elementname != "defs"]


def _drawn_points(shape: BaseShape) -> list[tuple[float, float]]:
    (polygon,) = _drawn(shape)
    assert isinstance(polygon, svgwrite.shapes.Polygon)
    return [(float(x), float(y)) for x, y in polygon.points]


@pytest.mark.parametrize("cls", POLYGON_SHAPES)
@pytest.mark.parametrize("angle", [0.0, 0.7])
def test_drawn_vertices_lie_on_or_inside_the_circle_of_diameter_size(cls, angle):
    shape = cls(3.0, 4.0, 10.0, angle=angle)
    distances = [math.hypot(x - 3.0, y - 4.0) for x, y in _drawn_points(shape)]
    assert max(distances) == pytest.approx(5.0)


def test_arrow_is_one_closed_polygon_of_seven_vertices():
    elements = _drawn(Arrow(0, 0, 10))
    (polygon,) = elements
    assert isinstance(polygon, svgwrite.shapes.Polygon)
    assert len(polygon.points) == 7


def test_arrow_tip_is_on_the_circle_along_the_angle():
    angle = 0.6
    points = _drawn_points(Arrow(2.0, 3.0, 10.0, angle=angle))
    tip = (2.0 + 5.0 * math.cos(angle), 3.0 + 5.0 * math.sin(angle))
    assert any(math.dist(p, tip) < 1e-9 for p in points)


def test_triangle_at_angle_zero_points_along_positive_x():
    points = _drawn_points(Triangle(0, 0, 10))
    assert max(points, key=lambda p: p[0]) == pytest.approx((5.0, 0.0))


@pytest.mark.parametrize("cls", ALL_SHAPES)
def test_outline_is_a_valid_polygon_anchored_inside_it(cls):
    outline = cls(1.0, 2.0, 10.0).outline()
    assert isinstance(outline, Polygon)
    assert outline.is_valid
    assert outline.contains(outline.representative_point())
    assert outline.contains(Polygon([(0.9, 1.9), (1.1, 1.9), (1.1, 2.1)]))


@pytest.mark.parametrize("cls", ALL_SHAPES)
@given(
    x=st.floats(-100, 100),
    y=st.floats(-100, 100),
    size=st.floats(0.5, 50),
    angle=st.floats(-7, 7),
)
def test_outline_extends_exactly_size_over_two_from_the_anchor(cls, x, y, size, angle):
    outline = cls(x, y, size, angle=angle).outline()
    farthest = max(math.hypot(px - x, py - y) for px, py in outline.exterior.coords)
    if cls is Circle:
        # The circle is a polygon that stays outside the true circle, so a check
        # on it never passes a true circle that crosses an edge.
        assert size / 2 <= farthest <= size / 2 / math.cos(math.pi / 64) * (1 + 1e-9)
    else:
        assert farthest == pytest.approx(size / 2, rel=1e-9)


@pytest.mark.parametrize(("cls", "order"), [(Square, 4), (Triangle, 1), (Arrow, 1), (Circle, None)])
def test_each_shape_states_its_rotational_symmetry(cls, order):
    assert cls.symmetry_order == order


@pytest.mark.parametrize(("cls", "order"), [(Square, 4), (Triangle, 1), (Arrow, 1)])
def test_symmetry_order_is_the_smallest_turn_that_maps_the_outline_onto_itself(cls, order):
    outline = cls(0, 0, 10).outline()

    def same_after_turn(turns: int) -> bool:
        turned = affinity.rotate(
            outline, 2 * math.pi * turns / order, origin=(0, 0), use_radians=True
        )
        return outline.symmetric_difference(turned).area < 1e-9

    assert same_after_turn(1)
    if order > 1:
        # a quarter turn of a square is the smallest; a fraction of it is not.
        half_step = affinity.rotate(outline, math.pi / order, origin=(0, 0), use_radians=True)
        assert outline.symmetric_difference(half_step).area > 1e-6
    else:
        turned = affinity.rotate(outline, 0.3, origin=(0, 0), use_radians=True)
        assert outline.symmetric_difference(turned).area > 1e-6


@pytest.mark.parametrize("cls", POLYGON_SHAPES)
@pytest.mark.parametrize("angle", [0.0, 0.7, 2.5])
def test_the_drawer_mirror_is_the_mirror_of_the_model_outline(cls, angle):
    """The drawer builds a shape at (x, -y) with angle -angle. Every outline is
    symmetric about its own axis, so that is the mirror of the model outline."""
    model = cls(4.0, 6.0, 8.0, angle=angle).outline()
    drawn = cls(4.0, -6.0, 8.0, angle=-angle).outline()
    mirrored = affinity.scale(model, xfact=1, yfact=-1, origin=(0, 0))
    assert mirrored.symmetric_difference(drawn).area < 1e-9
