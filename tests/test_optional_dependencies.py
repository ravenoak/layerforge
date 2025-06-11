import types
import pytest

from layerforge.utils.optional_dependencies import require_module


def test_require_module_success():
    mod = require_module("math", "Test")
    assert isinstance(mod, types.ModuleType)


def test_require_module_missing():
    with pytest.raises(ImportError) as exc:
        require_module("nonexistent_package_xyz", "MyFeature")
    assert str(exc.value) == "MyFeature requires the 'nonexistent_package_xyz' package. Install it via 'pip install nonexistent_package_xyz'."
