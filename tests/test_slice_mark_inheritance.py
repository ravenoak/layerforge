import random
import xml.etree.ElementTree as ET

import pytest

pytest.importorskip("trimesh")
pytest.importorskip("svgwrite")
pytest.importorskip("shapely")

from layerforge.cli import process_model


NS = {"svg": "http://www.w3.org/2000/svg"}


def _circle_position(svg_file: str) -> tuple[float, float] | None:
    tree = ET.parse(svg_file)
    root = tree.getroot()
    for circle in root.findall(".//svg:circle", NS):
        if circle.attrib.get("stroke") == "red":
            cx = float(circle.attrib["cx"])
            cy = float(circle.attrib["cy"])
            return cx, cy
    return None


def test_mark_shape_and_position_inherited(cylinder_stl, tmp_path):
    random.seed(0)
    out_dir = tmp_path / "svgs"
    process_model(
        stl_file=str(cylinder_stl),
        layer_height=2.5,
        output_folder=str(out_dir),
    )

    files = sorted(out_dir.glob("slice_*.svg"))
    assert files, "no svg files generated"

    positions = [pos for pos in (_circle_position(str(f)) for f in files) if pos]
    # There should be at least two slices with marks to compare
    assert len(positions) >= 2

    first = positions[0]
    for pos in positions[1:]:
        assert pos == first
