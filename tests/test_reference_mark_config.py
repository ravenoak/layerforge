import pytest

from layerforge.models.reference_marks import ReferenceMarkConfig


def test_empty_available_shapes_raises():
    with pytest.raises(ValueError):
        ReferenceMarkConfig(available_shapes=[])


@pytest.mark.parametrize("field", ["tolerance", "min_distance"])
def test_negative_values_raise_value_error(field):
    with pytest.raises(ValueError):
        ReferenceMarkConfig(**{field: -1})
