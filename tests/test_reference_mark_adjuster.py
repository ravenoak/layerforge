import pytest
from shapely.geometry import Polygon

import importlib.util
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
module_name = "layerforge.models.reference_marks.reference_mark_adjuster"
spec = importlib.util.spec_from_file_location(
    module_name, ROOT / "layerforge/models/reference_marks/reference_mark_adjuster.py"
)
module = importlib.util.module_from_spec(spec)

pkg_layerforge = types.ModuleType("layerforge")
pkg_models = types.ModuleType("layerforge.models")
pkg_ref = types.ModuleType("layerforge.models.reference_marks")
pkg_ref.__path__ = [str(ROOT / "layerforge/models/reference_marks")]
sys.modules.setdefault("layerforge", pkg_layerforge)
sys.modules.setdefault("layerforge.models", pkg_models)
sys.modules.setdefault("layerforge.models.reference_marks", pkg_ref)
sys.modules[module_name] = module
spec.loader.exec_module(module)  # type: ignore
ReferenceMarkAdjuster = module.ReferenceMarkAdjuster
ReferenceMark = module.ReferenceMark


def test_centroid_inside_kept():
    square = Polygon([(0, 0), (100, 0), (100, 100), (0, 100)])
    marks = [ReferenceMark(50, 50, 'circle', 3)]
    adjusted = ReferenceMarkAdjuster.adjust_marks(marks, [square], min_distance=10)
    assert adjusted == marks


def test_marks_near_boundary_removed():
    square = Polygon([(0, 0), (100, 0), (100, 100), (0, 100)])
    marks = [
        ReferenceMark(5, 5, 'circle', 3),    # inside but near boundary
        ReferenceMark(105, 50, 'square', 3), # outside near boundary
        ReferenceMark(95, 95, 'circle', 3),  # inside near boundary
    ]
    adjusted = ReferenceMarkAdjuster.adjust_marks(marks, [square], min_distance=10)
    assert adjusted == []
