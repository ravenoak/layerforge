import pytest

from layerforge.models.reference_marks import ReferenceMarkConfig


def test_empty_available_shapes_raises():
    with pytest.raises(ValueError):
        ReferenceMarkConfig(available_shapes=[])


@pytest.mark.parametrize("field", ["tolerance", "min_distance"])
def test_negative_values_raise_value_error(field):
    with pytest.raises(ValueError):
        ReferenceMarkConfig(**{field: -1})  # pyright: ignore[reportArgumentType]


@pytest.mark.parametrize("field", ["tolerance", "min_distance", "angle"])
@pytest.mark.parametrize("value", [float("nan"), float("inf")])
def test_non_finite_values_raise_value_error(field, value):
    with pytest.raises(ValueError):
        ReferenceMarkConfig(**{field: value})  # pyright: ignore[reportArgumentType]
