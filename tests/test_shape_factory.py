import pytest
from shapely.geometry import Point, Polygon

from layerforge.domain.shapes import registry
from layerforge.domain.shapes.base_shape import BaseShape
from layerforge.svg.drawing.shape_factory import ShapeFactory, register_shape


class MockShape(BaseShape):
    symmetry_order = 1

    def type(self) -> str:
        return "mock"

    def outline(self) -> Polygon:
        return Point(self.x, self.y).buffer(self.size / 2)


def test_register_and_retrieve_shape(monkeypatch):
    # Work on a copy, so the mock does not stay in the registry for other tests.
    monkeypatch.setattr(registry, "_SHAPE_REGISTRY", dict(registry._SHAPE_REGISTRY))
    register_shape("mock", MockShape)
    shape = ShapeFactory.get_shape("mock", 1, 2, 3)
    assert isinstance(shape, MockShape)
    assert shape.x == 1
    assert shape.y == 2
    assert shape.size == 3


def test_unknown_shape_error():
    with pytest.raises(ValueError):
        ShapeFactory.get_shape("unknown", 0, 0, 1)


class _NoOrderShape(BaseShape):
    def type(self) -> str:
        return "no-order"

    def outline(self) -> Polygon:
        return Point(self.x, self.y).buffer(self.size / 2)


class _OwnOrderShape(_NoOrderShape):
    symmetry_order = 6


class _UnlimitedShape(_NoOrderShape):
    symmetry_order = None


class _InheritsOrderShape(_OwnOrderShape):
    pass


@pytest.fixture
def scratch_registry(monkeypatch):
    # Work on a copy, so nothing registered here stays for other tests.
    monkeypatch.setattr(registry, "_SHAPE_REGISTRY", dict(registry._SHAPE_REGISTRY))
    return registry._SHAPE_REGISTRY


def test_register_shape_refuses_a_class_with_no_symmetry_order(scratch_registry):
    with pytest.raises(ValueError, match="_NoOrderShape.*symmetry_order"):
        register_shape("hexagon", _NoOrderShape)
    assert "hexagon" not in scratch_registry


def test_register_shape_refuses_a_class_that_only_inherits_an_order(scratch_registry):
    with pytest.raises(ValueError, match="_InheritsOrderShape"):
        register_shape("inherits", _InheritsOrderShape)


@pytest.mark.parametrize("cls, order", [(_OwnOrderShape, 6), (_UnlimitedShape, None)])
def test_register_shape_accepts_a_class_that_declares_its_order(scratch_registry, cls, order):
    register_shape("declared", cls)
    assert registry.shape_symmetry_order("declared") == order


def test_built_in_shapes_all_declare_their_order():
    for name in registry.registered_shapes():
        assert "symmetry_order" in vars(registry._shape_class(name)), name
