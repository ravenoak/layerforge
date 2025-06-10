import math
import pytest
pytest.importorskip("svgwrite")
pytest.importorskip("shapely")
import svgwrite
from layerforge.svg.drawing.strategies.arrow_strategy import ArrowDrawingStrategy
from layerforge.domain.shapes import Arrow


def _line_end(dwg: svgwrite.Drawing) -> tuple:
    line = [el for el in dwg.elements if isinstance(el, svgwrite.shapes.Line)][0]
    return float(line["x2"]), float(line["y2"])


def test_arrow_endpoint_degrees():
    arrow = Arrow(0, 0, 10, angle=90, color="purple")
    dwg = svgwrite.Drawing()
    ArrowDrawingStrategy().draw(dwg, arrow)
    x2, y2 = _line_end(dwg)
    line = [el for el in dwg.elements if isinstance(el, svgwrite.shapes.Line)][0]
    assert line["stroke"] == "purple"
    assert math.isclose(x2, 0.0, abs_tol=1e-6)
    assert math.isclose(y2, 10.0, abs_tol=1e-6)


def test_arrow_endpoint_radians():
    arrow = Arrow(0, 0, 10, angle=math.pi / 2)
    dwg = svgwrite.Drawing()
    ArrowDrawingStrategy().draw(dwg, arrow)
    x2, y2 = _line_end(dwg)
    assert math.isclose(x2, 0.0, abs_tol=1e-6)
    assert math.isclose(y2, 10.0, abs_tol=1e-6)
