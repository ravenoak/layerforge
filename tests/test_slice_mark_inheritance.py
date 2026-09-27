import xml.etree.ElementTree as ET

import pytest

pytest.importorskip("trimesh")
pytest.importorskip("svgwrite")
pytest.importorskip("shapely")

from layerforge.cli import process_model

NS = {"svg": "http://www.w3.org/2000/svg"}


def _mark_attributes(svg_file: str) -> dict[str, str] | None:
    """The attributes of the first mark, so its shape and its position are both compared."""
    root = ET.parse(svg_file).getroot()
    for element in root.iter():
        if element.attrib.get("class") == "mark":
            return dict(element.attrib)
    return None


def test_mark_shape_and_position_inherited(cylinder_stl, tmp_path):
    out_dir = tmp_path / "svgs"
    process_model(
        stl_file=str(cylinder_stl),
        layer_height=2.5,
        output_folder=str(out_dir),
    )

    files = sorted(out_dir.glob("slice_*.svg"))
    assert files, "no svg files generated"

    positions = [pos for pos in (_mark_attributes(str(f)) for f in files) if pos]
    # There should be at least two slices with marks to compare
    assert len(positions) >= 2

    first = positions[0]
    for pos in positions[1:]:
        assert pos == first
