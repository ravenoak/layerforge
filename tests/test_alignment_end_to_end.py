"""End to end: the layers a person cuts can be stacked in one way only (G-4, TR-2, #60).

The proof reads the written SVG files and nothing else. It does not call `check_alignment`
or any other function of the tool, so it holds if that check is wrong. For each model, every
two files of adjacent layers must hold a mark at identical coordinates, and that mark must be
a triangle with a direction: two equal sides and a third that differs. One such mark fixes
the position and, because no turn maps it onto itself, the rotation.
"""

import math
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import pytest

pytest.importorskip("trimesh")
import trimesh
from click.testing import CliRunner

from layerforge.cli import cli

SVG = "{http://www.w3.org/2000/svg}"


def _l_shape():
    """An L of two bars, 24 mm tall. One shell, triangulated by hand: no engine is installed."""
    vertices = np.array([(0, 0), (40, 0), (40, 15), (15, 15), (15, 40), (0, 40), (0, 15)], float)
    faces = np.array([(0, 1, 2), (0, 2, 3), (0, 3, 6), (6, 3, 4), (6, 4, 5)])
    return trimesh.creation.extrude_triangulation(vertices, faces, 24)


MODELS = {
    "cube": lambda: trimesh.creation.box(extents=(20, 20, 20)),
    "cylinder": lambda: trimesh.creation.cylinder(radius=30, height=30),
    "tube": lambda: trimesh.creation.annulus(r_min=12, r_max=20, height=30),
    "L-shaped part": _l_shape,
}


def _marks(path: Path) -> set[str]:
    """The `points` of every polygon mark of one file."""
    root = ET.parse(path).getroot()
    return {
        el.attrib["points"] for el in root.iter(f"{SVG}polygon") if el.attrib.get("class") == "mark"
    }


def _has_a_direction(points: str) -> bool:
    """A triangle with two equal sides and a third that differs has no turn onto itself."""
    corners = [tuple(map(float, pair.split(","))) for pair in points.split()]
    if len(corners) != 3:
        return False
    sides = [math.dist(corners[i], corners[(i + 1) % 3]) for i in range(3)]
    return len({round(side, 3) for side in sides}) == 2


@pytest.mark.parametrize("name", MODELS)
def test_every_two_adjacent_layers_share_a_mark_that_fixes_the_rotation(name, tmp_path):
    stl = tmp_path / "model.stl"
    MODELS[name]().export(stl)
    out = tmp_path / "out"

    result = CliRunner().invoke(cli, ["--stl-file", str(stl), "--output-folder", str(out)])

    assert result.exit_code == 0, result.stderr
    files = sorted(out.glob("slice_*.svg"))
    assert len(files) >= 2, "a model of one layer has no pair to prove"
    marks = [_marks(path) for path in files]
    for lower, upper, below, above in zip(files, files[1:], marks, marks[1:], strict=False):
        shared = below & above
        assert shared, f"{lower.name} and {upper.name} share no mark at identical coordinates"
        assert all(_has_a_direction(points) for points in shared), (
            f"{lower.name} and {upper.name}: a shared mark has no direction: {shared}"
        )
