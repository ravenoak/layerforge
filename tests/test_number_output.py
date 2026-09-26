"""The layer number in the SVG (TR-11, #75): the index, engraved, clear of every cut."""

import logging
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

pytest.importorskip("trimesh")
import trimesh
from click.testing import CliRunner
from shapely.geometry import Point, Polygon, box

from layerforge.cli import cli

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


def test_the_number_lies_clear_of_the_outline_and_the_marks(cube_stl, tmp_path):
    for root in _slices(cube_stl, tmp_path / "out"):
        (text,) = root.iter(f"{SVG}text")
        number = _number_box(text)
        (outline,) = [p for p in root.iter(f"{SVG}polygon") if p.get("class") == "outline"]
        points = [tuple(map(float, p.split(","))) for p in outline.get("points", "").split()]
        assert Polygon(points).contains(number)
        for circle in root.iter(f"{SVG}circle"):
            disc = Point(float(circle.get("cx", "")), float(circle.get("cy", ""))).buffer(
                float(circle.get("r", ""))
            )
            assert not number.intersects(disc)


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
            ],
        )

    assert result.exit_code == 0, result.output
    warnings = [r.getMessage() for r in caplog.records if "number" in r.getMessage()]
    assert len(warnings) == len(list(out.glob("slice_*.svg")))
    assert "--number-height" in warnings[0]
    assert "TR-" not in warnings[0]
    for path in out.glob("slice_*.svg"):
        assert list(ET.parse(path).getroot().iter(f"{SVG}text")), "the number is still drawn"
