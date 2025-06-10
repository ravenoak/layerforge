import pytest

from layerforge.svg.drawing.shape_factory import ShapeFactory, register_shape
from layerforge.domain.shapes.base_shape import BaseShape


class MockShape(BaseShape):
    def type(self) -> str:
        return "mock"


def test_register_and_retrieve_shape():
    register_shape("mock", MockShape)
    shape = ShapeFactory.get_shape("mock", 1, 2, 3)
    assert isinstance(shape, MockShape)
    assert shape.x == 1
    assert shape.y == 2
    assert shape.size == 3


def test_unknown_shape_error():
    with pytest.raises(ValueError):
        ShapeFactory.get_shape("unknown", 0, 0, 1)
