"""The layer number in the SVG (TR-11, #75): the index, engraved, clear of every cut."""

import logging
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

pytest.importorskip("trimesh")
import svgwrite
import trimesh
from click.testing import CliRunner
from shapely.geometry import Point, Polygon, box

from layerforge.cli import cli
from layerforge.models.slicing import Slice
from layerforge.svg.drawing.strategy_context import StrategyContext
from layerforge.svg.slice_svg_drawer import SliceSVGDrawer
from layerforge.utils.shape_strategies import register_shape_strategies

SVG = "{http://www.w3.org/2000/svg}"


@pytest.fixture
def cube_stl(tmp_path: Path) -> Path:
    mesh = trimesh.creation.box(extents=(40, 40, 20))
    mesh.apply_translation((0, 0, 10))
    path = tmp_path / "cube.stl"
    mesh.export(path)
    return path


def _slices(stl: Path, out: Path, *args: str) -> list[ET.Element]:
    result = CliRunner().invoke(
        cli, ["--stl-file", str(stl), "--layer-height", "5", "--output-folder", str(out), *args]
    )
    assert result.exit_code == 0, result.output
    return [ET.parse(path).getroot() for path in sorted(out.glob("slice_*.svg"))]


def test_the_text_is_the_index_alone(cube_stl, tmp_path):
    slices = _slices(cube_stl, tmp_path / "out")

    assert [[t.text for t in root.iter(f"{SVG}text")] for root in slices] == [
        [str(i)] for i in range(len(slices))
    ]


def test_the_number_is_centred_bold_sans_and_has_no_transform(cube_stl, tmp_path):
    for root in _slices(cube_stl, tmp_path / "out"):
        (text,) = root.iter(f"{SVG}text")
        assert text.get("text-anchor") == "middle"
        assert text.get("font-family") == "sans-serif"
        assert text.get("font-weight") == "bold"
        assert text.get("transform") is None
        assert text.get("stroke") is None


@pytest.mark.parametrize(
    ("args", "height"),
    [
        ([], 5.0),
        (["--number-height", "3"], 3.0),
    ],
)
def test_the_font_size_is_the_number_height(cube_stl, tmp_path, args, height):
    for root in _slices(cube_stl, tmp_path / "out", *args):
        (text,) = root.iter(f"{SVG}text")
        assert float(text.get("font-size", "")) == pytest.approx(height)


def test_the_number_height_follows_the_units(tmp_path):
    stl = tmp_path / "in.stl"
    mesh = trimesh.creation.box(extents=(4, 4, 1))
    mesh.export(stl)
    out = tmp_path / "out"
    result = CliRunner().invoke(
        cli, ["--stl-file", str(stl), "--units", "in", "--output-folder", str(out)]
    )
    assert result.exit_code == 0, result.output
    for path in out.glob("slice_*.svg"):
        (text,) = ET.parse(path).getroot().iter(f"{SVG}text")
        size = text.get("font-size", "")
        assert "e" not in size.lower()
        assert float(size) == pytest.approx(5 / 25.4)


def _number_box(text: ET.Element):
    """The box of a one-digit number, from its attributes: the text is centred at x."""
    x = float(text.get("x", ""))
    height = float(text.get("font-size", ""))
    baseline = float(text.get("y", ""))
    centre_y = baseline - 0.35 * height
    return box(x - 0.3 * height, centre_y - height / 2, x + 0.3 * height, centre_y + height / 2)


def _mark_holes(root: ET.Element) -> list[Polygon]:
    """The area of each drawn mark, whatever its shape (a polygon or a circle, #61)."""
    holes: list[Polygon] = []
    for el in root.iter():
        if el.get("class") != "mark":
            continue
        if el.tag == f"{SVG}circle":
            centre = Point(float(el.get("cx", "")), float(el.get("cy", "")))
            holes.append(centre.buffer(float(el.get("r", ""))))
        else:
            points = [tuple(map(float, p.split(","))) for p in el.get("points", "").split()]
            holes.append(Polygon(points))
    return holes


def test_the_number_lies_clear_of_the_outline_and_the_marks(cube_stl, tmp_path):
    for root in _slices(cube_stl, tmp_path / "out"):
        (text,) = root.iter(f"{SVG}text")
        number = _number_box(text)
        (outline,) = [p for p in root.iter(f"{SVG}polygon") if p.get("class") == "outline"]
        points = [tuple(map(float, p.split(","))) for p in outline.get("points", "").split()]
        assert Polygon(points).contains(number)
        holes = _mark_holes(root)
        assert holes, "there is a mark to keep clear of"
        for hole in holes:
            assert not number.intersects(hole)


def test_a_piece_too_small_for_the_number_warns_once_per_slice(tmp_path, caplog):
    stl = tmp_path / "small.stl"
    trimesh.creation.box(extents=(8, 8, 10)).export(stl)
    out = tmp_path / "out"

    with caplog.at_level(logging.WARNING):
        result = CliRunner().invoke(
            cli,
            [
                "--stl-file",
                str(stl),
                "--layer-height",
                "5",
                "--output-folder",
                str(out),
                "--mark-size",
                "1",
                # A circle covers more of a small piece than the triangle of the defaults.
                "--available-shapes",
                "circle",
            ],
        )

    assert result.exit_code == 0, result.output
    warnings = [r.getMessage() for r in caplog.records if "number" in r.getMessage()]
    assert len(warnings) == len(list(out.glob("slice_*.svg")))
    assert "--number-height" in warnings[0]
    assert "TR-" not in warnings[0]
    for path in out.glob("slice_*.svg"):
        assert list(ET.parse(path).getroot().iter(f"{SVG}text")), "the number is still drawn"


def test_a_slice_with_two_pieces_has_a_number_on_each(tmp_path):
    """Guard: each contour gets its own number, and the same text on both."""
    stl = tmp_path / "two.stl"
    left = trimesh.creation.box(extents=(30, 30, 20))
    right = trimesh.creation.box(extents=(30, 30, 20))
    right.apply_translation((60, 0, 0))
    trimesh.util.concatenate([left, right]).export(stl)

    for root in _slices(stl, tmp_path / "out"):
        texts = list(root.iter(f"{SVG}text"))
        assert len(texts) == 2
        assert len({t.text for t in texts}) == 1
        xs = sorted(float(t.get("x", "")) for t in texts)
        assert xs[1] - xs[0] > 30  # one on each piece


def test_the_config_file_sets_the_number_height(cube_stl, tmp_path):
    """Guard: the [number] key reaches the SVG, not only the settings."""
    cfg = tmp_path / "s.toml"
    cfg.write_text("[number]\nheight = 3\n")

    for root in _slices(cube_stl, tmp_path / "out", "--config", str(cfg)):
        (text,) = root.iter(f"{SVG}text")
        assert float(text.get("font-size", "")) == pytest.approx(3.0)


def _number_warnings(stl: Path, out: Path, caplog: pytest.LogCaptureFixture, *args: str):
    caplog.clear()
    with caplog.at_level(logging.WARNING):
        result = CliRunner().invoke(
            cli, ["--stl-file", str(stl), "--output-folder", str(out), *args]
        )
    assert result.exit_code == 0, result.output
    return [r.getMessage() for r in caplog.records if "number of slice" in r.getMessage()]


def test_the_warning_gives_a_height_that_makes_it_go_away(tmp_path, caplog):
    """The hint is a number that you can use: applied, no piece is left without room."""
    stl = tmp_path / "small.stl"
    trimesh.creation.box(extents=(8, 8, 10)).export(stl)

    messages = _number_warnings(stl, tmp_path / "a", caplog)
    assert len(messages) == 4  # one for each slice
    hints = {re.search(r"--number-height ([0-9.]+)", m)[1] for m in messages}  # type: ignore[index]
    hint = min(hints, key=float)
    assert 0 < float(hint) < 5

    assert _number_warnings(stl, tmp_path / "b", caplog, "--number-height", hint) == []


def test_a_10_mm_cube_at_the_defaults_leaves_the_number_room(tmp_path, caplog):
    """#61: the triangle of the defaults is smaller than the circle was.

    With circle marks the 10 mm cube warned in all 4 slices and needed a number of 4.83.
    """
    stl = tmp_path / "cube.stl"
    trimesh.creation.box(extents=(10, 10, 10)).export(stl)

    assert _number_warnings(stl, tmp_path / "a", caplog) == []
    circles = _number_warnings(stl, tmp_path / "b", caplog, "--available-shapes", "circle")
    assert len(circles) == 4


def test_the_warning_names_the_key_of_the_config_file_too(tmp_path, caplog):
    stl = tmp_path / "small.stl"
    trimesh.creation.box(extents=(8, 8, 10)).export(stl)

    (message, *_) = _number_warnings(stl, tmp_path / "a", caplog)

    assert "number.height" in message
    assert "--number-height" in message


def test_the_warning_says_when_no_height_fits(caplog):
    """A mark that covers a small piece leaves the number no room at any height."""
    ctx = StrategyContext()
    register_shape_strategies(ctx)
    piece = box(0, 0, 0.001, 0.001)  # the smallest test height, 0.005, is larger than the piece
    slice_obj = Slice(3, 0.0, [piece], layer_height=3.0)

    with caplog.at_level(logging.WARNING):
        SliceSVGDrawer.draw_slice(svgwrite.Drawing(), slice_obj, ctx)

    (message,) = [r.getMessage() for r in caplog.records]
    assert message.startswith("The number of slice 3 does not fit")
    assert "No height fits" in message
    assert "Try --number-height" not in message


@pytest.mark.parametrize(
    ("value", "text"),
    [
        (4.8349, "4.83"),
        (0.0123456, "0.0123"),
        (0.000393700787, "0.000393"),
        (5.0, "5"),
        (3210.5, "3210"),
        (30000.9, "30000"),
        (99.99, "99.9"),
    ],
)
def test_the_hint_is_rounded_down_to_three_digits_without_float_noise(value, text):
    assert SliceSVGDrawer._round_down(value) == text  # pyright: ignore[reportPrivateUsage]


def test_the_rounded_hint_never_exceeds_the_height_that_was_found():
    """A hint above the found height might not fit, and large values once printed float noise."""
    for value in (0.00031, 0.5, 4.8349, 49.999, 1234.5678, 28347477.493658833):
        text = SliceSVGDrawer._round_down(value)  # pyright: ignore[reportPrivateUsage]
        assert float(text) <= value
        assert float(text) > value * 0.99
        assert "e" not in text.lower()
        assert len(text.replace(".", "").lstrip("0")) <= 8
