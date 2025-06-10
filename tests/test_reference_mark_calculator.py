import importlib.util
import sys
import types
from pathlib import Path

import pytest
pytest.importorskip("shapely")
from shapely.geometry import Polygon, Point

ROOT = Path(__file__).resolve().parents[1]
module_name_slice = "layerforge.models.slicing.slice"
spec_slice = importlib.util.spec_from_file_location(
    module_name_slice, ROOT / "layerforge/models/slicing/slice.py"
)
module_slice = importlib.util.module_from_spec(spec_slice)

pkg_layerforge = types.ModuleType("layerforge")
pkg_models = types.ModuleType("layerforge.models")
pkg_models.__path__ = [str(ROOT / "layerforge/models")]
import importlib.machinery
pkg_models.__spec__ = importlib.machinery.ModuleSpec("layerforge.models", None, is_package=True)
pkg_ref = types.ModuleType("layerforge.models.reference_marks")
pkg_ref.__path__ = [str(ROOT / "layerforge/models/reference_marks")]
pkg_ref.__spec__ = importlib.machinery.ModuleSpec("layerforge.models.reference_marks", None, is_package=True)
pkg_utils = types.ModuleType("layerforge.utils")
pkg_utils.__path__ = [str(ROOT / "layerforge/utils")]

sys.modules["layerforge"] = pkg_layerforge
sys.modules["layerforge.models"] = pkg_models
sys.modules["layerforge.models.reference_marks"] = pkg_ref
sys.modules["layerforge.utils"] = pkg_utils
module_name_geom = "layerforge.utils.geometry"
spec_geom = importlib.util.spec_from_file_location(
    module_name_geom, ROOT / "layerforge/utils/geometry.py"
)
module_geom = importlib.util.module_from_spec(spec_geom)
sys.modules[module_name_geom] = module_geom
spec_geom.loader.exec_module(module_geom)  # type: ignore

pkg_utils.calculate_distance = module_geom.calculate_distance

pkg_ref.ReferenceMarkManager = None
pkg_ref.ReferenceMarkCalculator = None
pkg_ref.ReferenceMark = None
pkg_ref.ReferenceMarkAdjuster = None
pkg_ref.ReferenceMarkConfig = None

module_name_config = "layerforge.models.reference_marks.config"
spec_config = importlib.util.spec_from_file_location(
    module_name_config, ROOT / "layerforge/models/reference_marks/config.py"
)
module_config = importlib.util.module_from_spec(spec_config)
sys.modules[module_name_config] = module_config
spec_config.loader.exec_module(module_config)  # type: ignore
ReferenceMarkConfig = module_config.ReferenceMarkConfig
pkg_ref.ReferenceMarkConfig = ReferenceMarkConfig

sys.modules[module_name_slice] = module_slice

module_name_manager = "layerforge.models.reference_marks.reference_mark_manager"
spec_manager = importlib.util.spec_from_file_location(
    module_name_manager, ROOT / "layerforge/models/reference_marks/reference_mark_manager.py"
)
module_manager = importlib.util.module_from_spec(spec_manager)
sys.modules[module_name_manager] = module_manager
spec_manager.loader.exec_module(module_manager)  # type: ignore
ReferenceMarkManager = module_manager.ReferenceMarkManager
pkg_ref.ReferenceMarkManager = ReferenceMarkManager

module_name_calc = "layerforge.models.reference_marks.reference_mark_calculator"
spec_calc = importlib.util.spec_from_file_location(
    module_name_calc, ROOT / "layerforge/models/reference_marks/reference_mark_calculator.py"
)
module_calc = importlib.util.module_from_spec(spec_calc)
sys.modules[module_name_calc] = module_calc
spec_calc.loader.exec_module(module_calc)  # type: ignore
ReferenceMarkCalculator = module_calc.ReferenceMarkCalculator
pkg_ref.ReferenceMarkCalculator = ReferenceMarkCalculator

module_name_mark = "layerforge.models.reference_marks.reference_mark"
spec_mark = importlib.util.spec_from_file_location(
    module_name_mark, ROOT / "layerforge/models/reference_marks/reference_mark.py"
)
module_mark = importlib.util.module_from_spec(spec_mark)
sys.modules[module_name_mark] = module_mark
spec_mark.loader.exec_module(module_mark)  # type: ignore
ReferenceMark = module_mark.ReferenceMark
pkg_ref.ReferenceMark = ReferenceMark

module_name_adjuster = "layerforge.models.reference_marks.reference_mark_adjuster"
spec_adjuster = importlib.util.spec_from_file_location(
    module_name_adjuster, ROOT / "layerforge/models/reference_marks/reference_mark_adjuster.py"
)
module_adjuster = importlib.util.module_from_spec(spec_adjuster)
sys.modules[module_name_adjuster] = module_adjuster
spec_adjuster.loader.exec_module(module_adjuster)  # type: ignore
ReferenceMarkAdjuster = module_adjuster.ReferenceMarkAdjuster
pkg_ref.ReferenceMarkAdjuster = ReferenceMarkAdjuster

spec_slice.loader.exec_module(module_slice)  # type: ignore
Slice = module_slice.Slice


def test_inherit_mark_within_polygon():
    square = Polygon([(0, 0), (100, 0), (100, 100), (0, 100)])
    manager = ReferenceMarkManager()
    manager.add_or_update_mark(50, 50, "circle", 3)
    cfg = ReferenceMarkConfig(min_distance=10)
    sl = Slice(0, 0.0, [square], origin=(0, 0), mark_manager=manager, config=cfg)
    sl.process_reference_marks()
    assert len(sl.ref_marks) == 1
    assert sl.ref_marks[0].x == 50
    assert sl.ref_marks[0].y == 50


def test_generate_mark_respects_boundary():
    square = Polygon([(0, 0), (100, 0), (100, 100), (0, 100)])
    manager = ReferenceMarkManager()
    cfg = ReferenceMarkConfig(min_distance=10)
    sl = Slice(1, 0.0, [square], origin=(0, 0), mark_manager=manager, config=cfg)
    sl.process_reference_marks()
    assert len(sl.ref_marks) == 1
    pt = Point(sl.ref_marks[0].x, sl.ref_marks[0].y)
    assert square.contains(pt)
    assert square.boundary.distance(pt) >= 10
