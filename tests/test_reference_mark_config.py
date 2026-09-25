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


@pytest.mark.parametrize("value", [0.0, -1.0, float("nan"), float("inf")])
def test_size_must_be_positive_and_finite(value):
    with pytest.raises(ValueError):
        ReferenceMarkConfig(size=value)


def test_size_defaults_to_none():
    assert ReferenceMarkConfig().size is None
