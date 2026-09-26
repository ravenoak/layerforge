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


def test_size_min_distance_and_tolerance_are_derived_when_not_set():
    """TR-6 and TR-10: they come from the sheet, so the config holds no number for them."""
    cfg = ReferenceMarkConfig()
    assert (cfg.size, cfg.min_distance, cfg.tolerance) == (None, None, None)


def test_the_defaults_of_the_sheet_and_the_machine_are_the_sourced_numbers_of_tr_6():
    cfg = ReferenceMarkConfig()
    assert (cfg.kerf, cfg.min_hole_ratio, cfg.min_hole_kerf_factor) == (0.3, 1.0, 1.5)


@pytest.mark.parametrize(
    ("layer_height", "kerf", "expected"),
    [
        (3.0, 0.3, 3.0),  # the sheet term: 1 x 3
        (5.0, 0.3, 5.0),
        (0.2, 0.3, 0.45),  # the kerf term: 1.5 x 0.3 wins below a sheet of 0.45
        (3.0, 4.0, 6.0),
    ],
)
def test_the_minimum_size_is_the_larger_of_the_sheet_term_and_the_kerf_term(
    layer_height, kerf, expected
):
    assert ReferenceMarkConfig(kerf=kerf).min_size(layer_height) == pytest.approx(expected)


def test_resolved_fills_size_min_distance_and_tolerance_from_the_sheet():
    resolved = ReferenceMarkConfig().resolved(3.0)
    assert (resolved.size, resolved.min_distance) == (3.0, 3.0)
    assert resolved.tolerance == pytest.approx(0.3)


def test_resolved_keeps_every_value_that_is_set():
    resolved = ReferenceMarkConfig(size=8, min_distance=1, tolerance=2).resolved(3.0)
    assert (resolved.size, resolved.min_distance, resolved.tolerance) == (8, 1, 2)


def test_min_distance_and_tolerance_follow_a_size_that_is_set():
    resolved = ReferenceMarkConfig(size=8).resolved(3.0)
    assert resolved.min_distance == 8
    assert resolved.tolerance == pytest.approx(0.8)


def test_resolving_twice_changes_nothing_and_the_original_is_not_touched():
    cfg = ReferenceMarkConfig()
    once = cfg.resolved(3.0)
    assert once.resolved(3.0) == once
    assert cfg.size is None


@pytest.mark.parametrize(
    ("field", "value"),
    [("kerf", -1), ("min_hole_ratio", 0), ("min_hole_ratio", -1), ("min_hole_kerf_factor", -1)],
)
def test_the_sheet_and_machine_numbers_must_be_in_range(field, value):
    with pytest.raises(ValueError):
        ReferenceMarkConfig(**{field: value})  # pyright: ignore[reportArgumentType]


@pytest.mark.parametrize("field", ["kerf", "min_hole_ratio", "min_hole_kerf_factor"])
@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
def test_the_sheet_and_machine_numbers_must_be_finite(field, value):
    with pytest.raises(ValueError):
        ReferenceMarkConfig(**{field: value})  # pyright: ignore[reportArgumentType]
