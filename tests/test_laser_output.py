"""The SVG is laser output: one cut colour, a hairline stroke and no fill (TR-14, #83).

Every check runs through the command, so the tiny profile of svgwrite is in play. It rounds a
float attribute to 4 decimals, which matters for a hairline in inches.
"""

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

pytest.importorskip("trimesh")
import svgwrite
import trimesh
from click.testing import CliRunner

from layerforge.cli import cli
from layerforge.domain.shapes import Arrow, Circle, Square, Triangle
from layerforge.domain.shapes.base_shape import BaseShape
from layerforge.svg.drawing.strategies.arrow_strategy import ArrowDrawingStrategy
from layerforge.svg.drawing.strategies.circle_strategy import CircleDrawingStrategy
from layerforge.svg.drawing.strategies.square_strategy import SquareDrawingStrategy
from layerforge.svg.drawing.strategies.triangle_strategy import TriangleDrawingStrategy
from layerforge.svg.drawing.strategy_context import StrategyContext
from layerforge.utils.shape_strategies import register_shape_strategies

SVG = "{http://www.w3.org/2000/svg}"


@pytest.fixture
def cube_stl(tmp_path: Path) -> Path:
    """A 20 mm cube on the floor. At layer height 5 every slice gets marks."""
    mesh = trimesh.creation.box(extents=(20, 20, 20))
    mesh.apply_translation((0, 0, 10))
    path = tmp_path / "cube.stl"
    mesh.export(path)
    return path


def _slices(cube_stl: Path, out: Path, *args: str) -> list[ET.Element]:
    result = CliRunner().invoke(
        cli,
        ["--stl-file", str(cube_stl), "--layer-height", "5", "--output-folder", str(out), *args],
    )
    assert result.exit_code == 0, result.output
    return [ET.parse(path).getroot() for path in sorted(out.glob("slice_*.svg"))]


def _cut(root: ET.Element) -> list[ET.Element]:
    """Every element that is cut: the outlines and the marks."""
    return [el for tag in ("polygon", "circle") for el in root.iter(f"{SVG}{tag}")]


def test_every_cut_element_has_the_cut_colour_a_hairline_and_no_fill(cube_stl, tmp_path):
    slices = _slices(cube_stl, tmp_path / "out")

    assert slices
    for root in slices:
        cut = _cut(root)
        assert list(root.iter(f"{SVG}circle")), "no mark"
        for el in cut:
            assert el.get("stroke") == "red", el.attrib
            assert el.get("stroke-width") == "0.01", el.attrib
            assert el.get("fill") == "none", el.attrib


@pytest.mark.parametrize("shape", ["circle", "square", "triangle", "arrow"])
def test_a_mark_of_every_shape_is_drawn_in_the_cut_colour(cube_stl, tmp_path, shape):
    """Each shape used to have a colour of its own: red, blue, green and black."""
    slices = _slices(cube_stl, tmp_path / "out", "--available-shapes", shape)

    marks = [el for root in slices for el in _cut(root) if el.get("class") == "mark"]
    assert marks
    assert {(el.get("stroke"), el.get("stroke-width")) for el in marks} == {("red", "0.01")}


def test_outlines_and_marks_are_told_apart_by_class_and_not_by_colour(cube_stl, tmp_path):
    (root, *_) = _slices(cube_stl, tmp_path / "out")

    classes = [el.get("class") for el in _cut(root)]
    assert classes.count("outline") == 1
    assert classes.count("mark") >= 1
    assert set(classes) == {"outline", "mark"}


def test_the_root_holds_no_stroke_width_and_no_font_size(cube_stl, tmp_path):
    for root in _slices(cube_stl, tmp_path / "out"):
        assert root.get("stroke-width") is None
        assert root.get("font-size") is None


def test_the_number_is_engraved_and_has_no_stroke(cube_stl, tmp_path):
    for root in _slices(cube_stl, tmp_path / "out"):
        (text,) = root.iter(f"{SVG}text")
        assert text.get("fill") == "black"
        assert text.get("stroke") is None
        assert float(text.get("font-size", "0")) > 0


def test_the_colour_options_set_the_colours(cube_stl, tmp_path):
    slices = _slices(
        cube_stl, tmp_path / "out", "--cut-color", "#f00", "--engrave-color", "rgb(0,0,255)"
    )

    for root in slices:
        assert {el.get("stroke") for el in _cut(root)} == {"#f00"}
        (text,) = root.iter(f"{SVG}text")
        assert text.get("fill") == "rgb(0,0,255)"


def test_the_config_file_sets_the_colours_and_the_hairline(cube_stl, tmp_path):
    cfg = tmp_path / "s.toml"
    cfg.write_text('[output]\ncut_color = "blue"\nengrave_color = "green"\nhairline_width = 0.05\n')

    slices = _slices(cube_stl, tmp_path / "out", "--config", str(cfg))

    for root in slices:
        assert {(el.get("stroke"), el.get("stroke-width")) for el in _cut(root)} == {
            ("blue", "0.05")
        }
        (text,) = root.iter(f"{SVG}text")
        assert text.get("fill") == "green"


@pytest.mark.parametrize(("units", "width"), [("mm", 0.01), ("cm", 0.001), ("in", 0.01 / 25.4)])
def test_the_hairline_is_a_hundredth_of_a_millimetre_in_every_unit(
    cube_stl, tmp_path, units, width
):
    """svgwrite's tiny profile rounds a float to 4 decimals: 0.000394 inch would print 0.0004."""
    for root in _slices(cube_stl, tmp_path / "out", "--units", units):
        for el in _cut(root):
            text = el.get("stroke-width", "")
            assert "e" not in text.lower(), text
            assert float(text) == pytest.approx(width, rel=1e-6)
        (label,) = root.iter(f"{SVG}text")
        assert "e" not in label.get("font-size", "").lower()


@pytest.mark.parametrize(
    ("shape", "strategy"),
    [
        (Circle, CircleDrawingStrategy),
        (Square, SquareDrawingStrategy),
        (Triangle, TriangleDrawingStrategy),
        (Arrow, ArrowDrawingStrategy),
    ],
)
def test_a_strategy_returns_an_element_that_holds_no_style(shape, strategy):
    """The context styles every element, so no strategy can forget to (#83)."""
    element = strategy().element(svgwrite.Drawing(profile="tiny"), shape(1.0, 2.0, 4.0))

    assert not {"stroke", "stroke-width", "fill", "class"} & set(element.attribs)


def test_the_context_adds_the_style_to_the_element_and_the_drawing():
    context = StrategyContext()
    register_shape_strategies(context)
    dwg = svgwrite.Drawing(profile="tiny")
    shape: BaseShape = Square(1.0, 2.0, 4.0)

    context.draw(dwg, shape, stroke="red", stroke_width="0.01", fill="none", class_="mark")

    (element,) = [el for el in dwg.elements if el.elementname == "polygon"]
    assert element.attribs["stroke"] == "red"
    assert element.attribs["stroke-width"] == "0.01"
    assert element.attribs["fill"] == "none"
    assert element.attribs["class"] == "mark"
