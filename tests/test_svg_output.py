import pytest
pytest.importorskip("svgwrite")
pytest.importorskip("shapely")

import svgwrite
from shapely.geometry import box, Point

from layerforge.models.reference_marks import ReferenceMark, ReferenceMarkManager, ReferenceMarkConfig
from layerforge.models.slicing.slice import Slice
from layerforge.svg.slice_svg_drawer import SliceSVGDrawer
from layerforge.svg.svg_generator import SVGGenerator
from layerforge.writers.svg_writer import SVGFileWriter, SVGWriter
from layerforge.svg.drawing.strategy_context import StrategyContext
from layerforge.utils.shape_strategies import register_shape_strategies


class CaptureWriter(SVGFileWriter):
    """SVGFileWriter that also stores drawings in memory for inspection."""

    def __init__(self):
        self.saved: list[svgwrite.Drawing] = []

    def write(self, svg: svgwrite.Drawing, output_folder: str, index: int) -> None:  # type: ignore[override]
        super().write(svg, output_folder, index)
        self.saved.append(svg)


def _create_slice(idx: int, shape: str) -> Slice:
    poly = box(0, 0, 10, 10)
    manager = ReferenceMarkManager()
    cfg = ReferenceMarkConfig()
    sl = Slice(idx, 0.0, [poly], origin=(0, 0), mark_manager=manager, config=cfg)
    sl.ref_marks = [ReferenceMark(x=5, y=5, shape=shape, size=4)]
    return sl


def _has_shape(dwg: svgwrite.Drawing, cls: type, stroke: str | None = None) -> bool:
    """Return True if ``dwg`` contains an element of ``cls`` with ``stroke``."""
    for el in dwg.elements:
        if isinstance(el, cls):
            attr = getattr(el, "attribs", {})
            if stroke is None or attr.get("stroke") == stroke:
                return True
    return False


def _text_positions(dwg: svgwrite.Drawing) -> list[tuple[float, float]]:
    """Return the (x, y) positions of text elements in ``dwg``."""
    coords: list[tuple[float, float]] = []
    for el in dwg.elements:
        if isinstance(el, svgwrite.text.Text):
            attr = getattr(el, "attribs", {})
            x = float(attr.get("x"))
            y = float(attr.get("y"))
            coords.append((x, y))
    return coords


def test_draw_slice_adds_expected_shapes():
    ctx = StrategyContext()
    register_shape_strategies(ctx)
    slice_obj = _create_slice(0, "circle")
    slice_obj.ref_marks.extend([
        ReferenceMark(5, 6, "square", 4),
        ReferenceMark(6, 6, "triangle", 4),
    ])
    dwg = svgwrite.Drawing()
    SliceSVGDrawer.draw_slice(dwg, slice_obj, ctx)

    assert _has_shape(dwg, svgwrite.shapes.Circle, "red")
    assert _has_shape(dwg, svgwrite.shapes.Rect, "blue")
    assert _has_shape(dwg, svgwrite.shapes.Polygon, "green")
    assert _has_shape(dwg, svgwrite.shapes.Polygon, "black")  # contour


def test_svg_generator_writes_files_and_captures(tmp_path):
    ctx = StrategyContext()
    register_shape_strategies(ctx)
    writer = CaptureWriter()
    gen = SVGGenerator(str(tmp_path), writer, ctx)
    slices = [
        _create_slice(1, "circle"),
        _create_slice(2, "square"),
        _create_slice(3, "triangle"),
    ]
    gen.generate_svgs(slices)

    for idx in range(1, 4):
        path = tmp_path / f"slice_{idx:03d}.svg"
        assert path.exists()

    assert _has_shape(writer.saved[0], svgwrite.shapes.Circle)
    assert _has_shape(writer.saved[1], svgwrite.shapes.Rect)
    assert _has_shape(writer.saved[2], svgwrite.shapes.Polygon, "green")


def test_label_inside_slice_polygon():
    ctx = StrategyContext()
    register_shape_strategies(ctx)
    slice_obj = _create_slice(0, "circle")
    dwg = svgwrite.Drawing()
    SliceSVGDrawer.draw_slice(dwg, slice_obj, ctx)

    positions = _text_positions(dwg)
    assert positions
    poly = slice_obj.contours[0]
    for x, y in positions:
        assert poly.contains(Point(x, y))
