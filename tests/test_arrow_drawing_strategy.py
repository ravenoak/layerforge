import math

import pytest

pytest.importorskip("svgwrite")
pytest.importorskip("shapely")
import svgwrite
import svgwrite.shapes

from layerforge.domain.shapes import Arrow
from layerforge.svg.drawing.strategies.arrow_strategy import ArrowDrawingStrategy


def _outline(arrow: Arrow) -> svgwrite.shapes.Polygon:
    polygon = ArrowDrawingStrategy().element(svgwrite.Drawing(), arrow)
    assert isinstance(polygon, svgwrite.shapes.Polygon)
    return polygon


def test_arrow_angle_is_always_radians():
    """A large value is a large number of radians, not degrees."""
    tip = _outline(Arrow(0, 0, 10, angle=90)).points[0]
    assert tip == pytest.approx((5 * math.cos(90), 5 * math.sin(90)))


def test_arrow_tip_radians():
    tip = _outline(Arrow(0, 0, 10, angle=math.pi / 2)).points[0]
    assert tip == pytest.approx((0.0, 5.0), abs=1e-9)
