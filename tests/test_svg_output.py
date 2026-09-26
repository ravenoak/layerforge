import pytest

pytest.importorskip("svgwrite")
pytest.importorskip("shapely")

import math

import svgwrite
import svgwrite.shapes
import svgwrite.text
from shapely.geometry import Point, Polygon, box

from layerforge.models.reference_marks import (
    ReferenceMark,
    ReferenceMarkConfig,
    ReferenceMarkManager,
)
from layerforge.models.slicing.slice import Slice
from layerforge.svg.drawing.strategy_context import StrategyContext
from layerforge.svg.slice_svg_drawer import SliceSVGDrawer
from layerforge.svg.svg_generator import SVGGenerator
from layerforge.utils.shape_strategies import register_shape_strategies
from layerforge.writers.svg_writer import SVGFileWriter


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
    sl = Slice(idx, 0.0, [poly], mark_manager=manager, config=cfg, layer_height=3.0)
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
            x = float(attr["x"])
            y = float(attr["y"])
            coords.append((x, y))
    return coords


def test_draw_slice_adds_expected_shapes():
    ctx = StrategyContext()
    register_shape_strategies(ctx)
    slice_obj = _create_slice(0, "circle")
    slice_obj.ref_marks.extend(
        [
            ReferenceMark(5, 6, "square", 4),
            ReferenceMark(6, 6, "triangle", 4),
        ]
    )
    dwg = svgwrite.Drawing()
    SliceSVGDrawer.draw_slice(dwg, slice_obj, ctx)

    assert _has_shape(dwg, svgwrite.shapes.Circle, "red")
    assert _has_shape(dwg, svgwrite.shapes.Polygon, "blue")  # square
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
    assert _has_shape(writer.saved[1], svgwrite.shapes.Polygon, "blue")
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
        # SVG's y axis points down, so the drawing shows the model's y negated.
        assert poly.contains(Point(x, -y))


def _plate_with_hole_slice() -> Slice:
    hole = [(20, 20), (80, 20), (80, 80), (20, 80)]
    plate = Polygon([(0, 0), (100, 0), (100, 100), (0, 100)], [hole])
    manager = ReferenceMarkManager()
    return Slice(
        0,
        0.0,
        [plate],
        mark_manager=manager,
        config=ReferenceMarkConfig(),
        layer_height=3.0,
    )


def test_holes_are_drawn_as_outlines():
    ctx = StrategyContext()
    register_shape_strategies(ctx)
    dwg = svgwrite.Drawing()
    SliceSVGDrawer.draw_slice(dwg, _plate_with_hole_slice(), ctx)

    outlines = [
        el
        for el in dwg.elements
        if isinstance(el, svgwrite.shapes.Polygon) and el.attribs.get("stroke") == "black"
    ]
    assert len(outlines) == 2


def test_label_is_not_placed_in_a_hole():
    ctx = StrategyContext()
    register_shape_strategies(ctx)
    slice_obj = _plate_with_hole_slice()
    dwg = svgwrite.Drawing()
    SliceSVGDrawer.draw_slice(dwg, slice_obj, ctx)

    (x, y) = _text_positions(dwg)[0]
    assert slice_obj.contours[0].contains(Point(x, -y))


def _draw(polygon: Polygon, *marks: ReferenceMark) -> svgwrite.Drawing:
    ctx = StrategyContext()
    register_shape_strategies(ctx)
    sl = Slice(
        0,
        0.0,
        [polygon],
        mark_manager=ReferenceMarkManager(),
        config=None,
        layer_height=3.0,
    )
    sl.ref_marks = list(marks)
    dwg = svgwrite.Drawing()
    SliceSVGDrawer.draw_slice(dwg, sl, ctx)
    return dwg


def test_y_axis_is_flipped_for_outlines():
    """SVG's y axis points down; the model's points up. An L shape keeps its handedness."""
    l_shape = Polygon([(0, 0), (10, 0), (10, 2), (2, 2), (2, 10), (0, 10)])
    dwg = _draw(l_shape)
    (outline,) = [el for el in dwg.elements if isinstance(el, svgwrite.shapes.Polygon)]
    assert {(0, 0), (10, 0), (10, -2), (2, -2), (2, -10), (0, -10)} <= set(outline.points)


def test_y_axis_is_flipped_for_marks():
    dwg = _draw(box(0, 0, 20, 20), ReferenceMark(x=5, y=6, shape="circle", size=4))
    (circle,) = [el for el in dwg.elements if isinstance(el, svgwrite.shapes.Circle)]
    assert (circle.attribs["cx"], circle.attribs["cy"]) == (5, -6)


def test_arrow_pointing_up_in_the_model_points_up_on_screen():
    arrow = ReferenceMark(x=5, y=6, shape="arrow", size=4, angle=math.pi / 2)
    dwg = _draw(box(0, 0, 20, 20), arrow)
    # The contour is a 4-point polygon; the arrow is a closed 7-point polygon.
    (outline,) = [
        el for el in dwg.elements if isinstance(el, svgwrite.shapes.Polygon) and len(el.points) == 7
    ]
    # The tip is a radius (size / 2) from the anchor (5, -6), straight up on screen.
    tip = min(outline.points, key=lambda p: p[1])
    assert tip == pytest.approx((5, -8))


def _view_box(dwg: svgwrite.Drawing) -> tuple[float, ...]:
    return tuple(float(v) for v in dwg.attribs["viewBox"].split(","))


def test_every_svg_has_the_same_view_box_around_all_slices(tmp_path):
    ctx = StrategyContext()
    register_shape_strategies(ctx)
    writer = CaptureWriter()
    big, small = box(90, 40, 110, 60), box(95, 45, 105, 55)
    slices = [
        Slice(
            i,
            0.0,
            [poly],
            ReferenceMarkManager(),
            ReferenceMarkConfig(),
            layer_height=3.0,
        )
        for i, poly in enumerate([big, small])
    ]
    SVGGenerator(str(tmp_path), writer, ctx).generate_svgs(slices)

    # The union is 20 x 20 at x 90..110 and y -60..-40, plus a 5% margin (1) each side.
    assert [_view_box(d) for d in writer.saved] == [(89, -61, 22, 22)] * 2


def test_no_view_box_when_nothing_was_cut(tmp_path):
    ctx = StrategyContext()
    register_shape_strategies(ctx)
    writer = CaptureWriter()
    empty = Slice(0, 0.0, [], ReferenceMarkManager(), ReferenceMarkConfig(), layer_height=3.0)
    SVGGenerator(str(tmp_path), writer, ctx).generate_svgs([empty])
    assert "viewBox" not in writer.saved[0].attribs


def _generate(tmp_path, polygons, **kwargs):
    ctx = StrategyContext()
    register_shape_strategies(ctx)
    writer = CaptureWriter()
    slices = [
        Slice(i, 0.0, [poly], ReferenceMarkManager(), ReferenceMarkConfig(), layer_height=3.0)
        for i, poly in enumerate(polygons)
    ]
    SVGGenerator(str(tmp_path), writer, ctx, **kwargs).generate_svgs(slices)
    return writer.saved


@pytest.mark.parametrize("units", ["mm", "cm", "in"])
def test_svg_width_and_height_are_the_view_box_size_in_the_unit(tmp_path, units):
    """A laser program reads the size from width and height, so they must match the view box."""
    # 10.1 x 3.3 gives view box numbers that are not round, so a rounded width would differ.
    saved = _generate(tmp_path, [box(0, 0, 10.1, 3.3), box(1, 1, 2, 2)], units=units)

    for dwg in saved:
        _, _, view_width, view_height = dwg.attribs["viewBox"].split(",")
        assert dwg.attribs["width"] == f"{view_width}{units}"
        assert dwg.attribs["height"] == f"{view_height}{units}"


def test_svg_size_is_in_millimetres_by_default(tmp_path):
    (dwg,) = _generate(tmp_path, [box(0, 0, 10, 10)])

    assert dwg.attribs["width"].endswith("mm")
    assert dwg.attribs["height"].endswith("mm")


def test_every_svg_has_the_same_physical_size(tmp_path):
    saved = _generate(tmp_path, [box(0, 0, 40, 20), box(10, 5, 20, 10)], units="cm")

    assert len({(d.attribs["width"], d.attribs["height"]) for d in saved}) == 1


def test_svg_without_a_view_box_keeps_a_relative_size(tmp_path):
    ctx = StrategyContext()
    register_shape_strategies(ctx)
    writer = CaptureWriter()
    empty = Slice(0, 0.0, [], ReferenceMarkManager(), ReferenceMarkConfig(), layer_height=3.0)

    SVGGenerator(str(tmp_path), writer, ctx, units="cm").generate_svgs([empty])

    assert writer.saved[0].attribs["width"] == "100%"
    assert writer.saved[0].attribs["height"] == "100%"
