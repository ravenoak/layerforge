"""Run the installed ``layerforge`` console script on a generated mesh."""

import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

pytest.importorskip("trimesh")
import trimesh

from layerforge.models.slicing.slicer_service import SlicerService

SVG = "{http://www.w3.org/2000/svg}"
LAYER_HEIGHT = 5.0


@pytest.fixture(params=[10.0, 0.0], ids=["on-the-floor", "centred-on-origin"])
def box_stl(tmp_path: Path, request: pytest.FixtureRequest) -> Path:
    """A 20 mm cube, either sitting on z=0 or centred on the origin.

    The centre height is ``request.param``.
    """
    mesh = trimesh.creation.box(extents=(20, 20, 20))
    mesh.apply_translation((0, 0, request.param))
    path = tmp_path / "box.stl"
    mesh.export(path)
    return path


def _run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    exe = shutil.which("layerforge", path=str(Path(sys.executable).parent))
    if exe is None:
        pytest.skip("the layerforge console script is not installed")
    return subprocess.run([exe, *args], capture_output=True, text=True, check=False)


@pytest.mark.parametrize(
    ("extra_args", "final_height"),
    [
        ([], 20.0),
        # A 10 mm cube is 5 mm from centre to edge, so shrink the default
        # 10 mm mark clearance or no mark fits.
        (["--target-height", "10", "--mark-min-distance", "2"], 10.0),
        (["--scale-factor", "0.5", "--mark-min-distance", "2"], 10.0),
    ],
)
def test_cli_writes_one_svg_per_slice(
    box_stl: Path, tmp_path: Path, extra_args: list[str], final_height: float
) -> None:
    out = tmp_path / "out"
    result = _run_cli(
        "--stl-file",
        str(box_stl),
        "--layer-height",
        str(LAYER_HEIGHT),
        "--output-folder",
        str(out),
        *extra_args,
    )
    assert result.returncode == 0, result.stderr

    # Scaling is about the origin, so the lowest point scales too.
    bottom = float(trimesh.load_mesh(box_stl).bounds[0][2]) * final_height / 20.0
    positions = SlicerService.calculate_slice_positions(bottom, bottom + final_height, LAYER_HEIGHT)
    files = sorted(out.glob("slice_*.svg"))
    assert [f.name for f in files] == [f"slice_{i:03d}.svg" for i in range(len(positions))]

    marks: list[tuple[str | None, str | None]] = []
    view_boxes: set[str | None] = set()
    for index, path in enumerate(files):
        root = ET.parse(path).getroot()
        view_boxes.add(root.get("viewBox"))
        contours = [p for p in root.iter(f"{SVG}polygon") if p.get("stroke") == "black"]
        circles = list(root.iter(f"{SVG}circle"))
        labels = [t.text for t in root.iter(f"{SVG}text")]
        assert contours, f"{path.name} has no contour"
        assert circles, f"{path.name} has no reference mark"
        assert f"Slice {index}" in labels
        marks.append((circles[0].get("cx"), circles[0].get("cy")))

    # All layers share one frame, so they can be laid over each other.
    assert len(view_boxes) == 1
    assert None not in view_boxes

    # The first mark is inherited by every later slice at the same position.
    assert len(set(marks)) == 1


def test_cli_missing_file_fails_without_output(tmp_path: Path) -> None:
    out = tmp_path / "out"
    result = _run_cli("--stl-file", str(tmp_path / "missing.stl"), "--output-folder", str(out))
    assert result.returncode != 0
    assert not list(out.glob("*.svg"))
