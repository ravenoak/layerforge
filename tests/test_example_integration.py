import pytest
pytest.importorskip("trimesh")
pytest.importorskip("svgwrite")
pytest.importorskip("shapely")

from scripts.simple_mesh_example import run_example


def test_example_generates_svgs(tmp_path):
    out_dir = tmp_path / "svgs"
    run_example(output_folder=str(out_dir))

    files = sorted(out_dir.glob("slice_*.svg"))
    assert files, "no svg files generated"

    found_mark = False
    for fp in files:
        txt = fp.read_text()
        if any(color in txt for color in ["stroke=\"red\"", "stroke=\"blue\"", "stroke=\"green\""]):
            found_mark = True
            break
    assert found_mark, "no reference marks found in SVGs"
