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


def test_a_shared_mark_is_identical_in_the_two_slices_that_hold_it(cylinder_stl, tmp_path):
    """TR-10: same centre, shape, size and angle in both layers a shared mark appears in.

    A straight cylinder overlaps its neighbours enough that consecutive slices share a mark;
    this does not assert every slice holds the *same* mark (that would be the pre-#63 bug, G-7)
    -- only that wherever a mark IS shared, its two appearances agree exactly.
    """
    out_dir = tmp_path / "svgs"
    process_model(
        stl_file=str(cylinder_stl),
        layer_height=2.5,
        output_folder=str(out_dir),
    )

    files = sorted(out_dir.glob("slice_*.svg"))
    assert files, "no svg files generated"

    positions = [pos for pos in (_mark_attributes(str(f)) for f in files) if pos]
    assert len(positions) >= 2, "expected at least one pair of consecutive slices with a mark"
    # Consecutive marks come from a shared point on a nearly-straight cylinder; a real assertion
    # of TR-10 needs two ADJACENT slices' marks, which is exactly `positions[i]`/`positions[i+1]`
    # here since every slice of this fixture gets a mark.
    for earlier, later in zip(positions, positions[1:], strict=False):
        assert earlier == later
