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
        # A 10 mm cube is 5 mm from centre to edge. The default mark is as big as the layer
        # height (5), and with its web (2.5) it does not fit, so use a smaller mark.
        (["--target-height", "10", "--mark-size", "3"], 10.0),
        (["--scale-factor", "0.5", "--mark-size", "3"], 10.0),
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
        contours = [p for p in root.iter(f"{SVG}polygon") if p.get("class") == "outline"]
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


@pytest.mark.parametrize(
    ("file_units", "option_units", "expected"),
    [
        (None, None, "mm"),
        (None, "in", "in"),
        ("cm", None, "cm"),
        ("cm", "in", "in"),
    ],
)
def test_cli_svg_size_is_the_view_box_size_in_the_unit(
    box_stl: Path,
    tmp_path: Path,
    file_units: str | None,
    option_units: str | None,
    expected: str,
) -> None:
    """A laser program reads the size from width and height (TR-13, #74)."""
    out = tmp_path / "out"
    args = ["--stl-file", str(box_stl), "--layer-height", str(LAYER_HEIGHT)]
    args += ["--output-folder", str(out)]
    if file_units is not None:
        config = tmp_path / "settings.toml"
        config.write_text(f'units = "{file_units}"\n')
        args += ["--config", str(config)]
    if option_units is not None:
        args += ["--units", option_units]

    result = _run_cli(*args)

    assert result.returncode == 0, result.stderr
    files = sorted(out.glob("slice_*.svg"))
    assert files
    sizes = set()
    for path in files:
        root = ET.parse(path).getroot()
        view_box = root.get("viewBox")
        assert view_box is not None
        _, _, view_width, view_height = view_box.split(",")
        assert root.get("width") == f"{view_width}{expected}"
        assert root.get("height") == f"{view_height}{expected}"
        sizes.add((root.get("width"), root.get("height")))
    assert len(sizes) == 1  # every layer has the same size, so they print at the same scale


def test_cli_missing_file_fails_without_output(tmp_path: Path) -> None:
    out = tmp_path / "out"
    result = _run_cli("--stl-file", str(tmp_path / "missing.stl"), "--output-folder", str(out))
    assert result.returncode != 0
    assert not list(out.glob("*.svg"))


def test_cli_warns_when_no_mark_fits(box_stl: Path, tmp_path: Path) -> None:
    """At layer height 5 the default mark (size 5, web 2.5) does not fit a 10 mm cube."""
    out = tmp_path / "out"
    result = _run_cli(
        "--stl-file",
        str(box_stl),
        "--layer-height",
        str(LAYER_HEIGHT),
        "--output-folder",
        str(out),
        "--target-height",
        "10",
    )
    assert result.returncode == 0, result.stderr
    assert "--mark-min-distance" in result.stderr
    assert len(list(out.glob("slice_*.svg"))) == 2


def test_cli_a_10_mm_cube_gets_marks_with_the_default_options(tmp_path: Path) -> None:
    """#76: the default minimum distance is the mark size, so a small model is not skipped.

    Before, the default of 10 was larger than the 5 mm from the centre to the edge, and this
    cube got no marks.
    """
    stl = tmp_path / "cube.stl"
    trimesh.creation.box(extents=(10, 10, 10)).export(stl)
    out = tmp_path / "out"

    result = _run_cli("--stl-file", str(stl), "--output-folder", str(out))

    assert result.returncode == 0, result.stderr
    assert "--mark-min-distance" not in result.stderr
    files = sorted(out.glob("slice_*.svg"))
    assert len(files) == 4  # 10 mm at the default sheet of 3 mm
    for path in files:
        assert list(ET.parse(path).getroot().iter(f"{SVG}circle")), f"{path.name} has no mark"


def test_cli_units_in_give_marks_of_a_sensible_size_without_setting_a_length(
    tmp_path: Path,
) -> None:
    """#62: with --units in the default sheet is 3 mm in inches, so a 1 inch cube gets marks."""
    stl = tmp_path / "inch.stl"
    trimesh.creation.box(extents=(1, 1, 1)).export(stl)
    out = tmp_path / "out"

    result = _run_cli("--stl-file", str(stl), "--units", "in", "--output-folder", str(out))

    assert result.returncode == 0, result.stderr
    assert "--mark-min-distance" not in result.stderr
    files = sorted(out.glob("slice_*.svg"))
    assert files
    for path in files:
        radii = [float(c.attrib["r"]) for c in ET.parse(path).getroot().iter(f"{SVG}circle")]
        assert radii == [pytest.approx(3 / 25.4 / 2, rel=1e-3)], path.name


def test_cli_a_mark_size_below_the_least_hole_size_warns_and_still_runs(
    box_stl: Path, tmp_path: Path
) -> None:
    """TR-6: the person knows the machine, so a small size is a warning and not an error."""
    out = tmp_path / "out"

    result = _run_cli("--stl-file", str(box_stl), "--mark-size", "1", "--output-folder", str(out))

    assert result.returncode == 0, result.stderr
    assert "below the least hole size" in result.stderr
    assert result.stderr.count("below the least hole size") == 1
    assert list(out.glob("slice_*.svg"))


def test_cli_config_file_sets_every_mark_size(box_stl: Path, tmp_path: Path) -> None:
    """A circle's radius is half its size, so size 2.5 gives r = 1.25 in every SVG."""
    config = tmp_path / "settings.toml"
    config.write_text(
        'layer_height = 5\n[marks]\nsize = 2.5\nmin_distance = 2\nshapes = ["circle"]\n'
    )
    out = tmp_path / "out"
    result = _run_cli(
        "--stl-file", str(box_stl), "--config", str(config), "--output-folder", str(out)
    )
    assert result.returncode == 0, result.stderr
    radii = {
        float(circle.attrib["r"])
        for svg in out.glob("slice_*.svg")
        for circle in ET.parse(svg).getroot().iter(f"{SVG}circle")
    }
    assert radii == {1.25}
