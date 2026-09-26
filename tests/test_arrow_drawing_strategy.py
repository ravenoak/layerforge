import math

import pytest

pytest.importorskip("svgwrite")
pytest.importorskip("shapely")
import svgwrite
import svgwrite.shapes

from layerforge.domain.shapes import Arrow
from layerforge.svg.drawing.strategies.arrow_strategy import ArrowDrawingStrategy


def _outline(dwg: svgwrite.Drawing) -> svgwrite.shapes.Polygon:
    (polygon,) = [el for el in dwg.elements if isinstance(el, svgwrite.shapes.Polygon)]
    return polygon


def test_arrow_angle_is_always_radians():
    """A large value is a large number of radians, not degrees."""
    arrow = Arrow(0, 0, 10, angle=90, color="purple")
    dwg = svgwrite.Drawing()
    ArrowDrawingStrategy().draw(dwg, arrow)
    polygon = _outline(dwg)
    assert polygon["stroke"] == "purple"
    tip = polygon.points[0]
    assert tip == pytest.approx((5 * math.cos(90), 5 * math.sin(90)))


def test_arrow_tip_radians():
    arrow = Arrow(0, 0, 10, angle=math.pi / 2)
    dwg = svgwrite.Drawing()
    ArrowDrawingStrategy().draw(dwg, arrow)
    assert _outline(dwg).points[0] == pytest.approx((0.0, 5.0), abs=1e-9)
