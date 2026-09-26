import pytest
from shapely.geometry import Point, Polygon

from layerforge.domain.shapes.base_shape import BaseShape
from layerforge.svg.drawing import shape_factory
from layerforge.svg.drawing.shape_factory import ShapeFactory, register_shape


class MockShape(BaseShape):
    def type(self) -> str:
        return "mock"

    def outline(self) -> Polygon:
        return Point(self.x, self.y).buffer(self.size / 2)


def test_register_and_retrieve_shape(monkeypatch):
    # Work on a copy, so the mock does not stay in the registry for other tests.
    monkeypatch.setattr(shape_factory, "_SHAPE_REGISTRY", dict(shape_factory._SHAPE_REGISTRY))
    register_shape("mock", MockShape)
    shape = ShapeFactory.get_shape("mock", 1, 2, 3)
    assert isinstance(shape, MockShape)
    assert shape.x == 1
    assert shape.y == 2
    assert shape.size == 3


def test_unknown_shape_error():
    with pytest.raises(ValueError):
        ShapeFactory.get_shape("unknown", 0, 0, 1)
