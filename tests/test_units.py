import pytest

from layerforge.units import from_mm, plain_number


@pytest.mark.parametrize(("units", "expected"), [("mm", 3.0), ("cm", 0.3), ("in", 3 / 25.4)])
def test_from_mm_states_a_millimetre_length_in_the_unit(units, expected):
    assert from_mm(units, 3.0) == pytest.approx(expected)


@pytest.mark.parametrize(
    ("value", "text"),
    [
        (0.01, "0.01"),
        (3.0, "3.0"),
        (25.4, "25.4"),
        (1e-05, "0.00001"),  # str(1e-05) is '1e-05', which a laser program may not read
        (1e-07, "0.0000001"),
        (1e16, "10000000000000000"),
        (0.000393700787, "0.000393700787"),  # 0.01 mm in inches; nothing is rounded
        (123456789.123, "123456789.123"),
    ],
)
def test_plain_number_never_uses_an_exponent(value, text):
    assert plain_number(value) == text
    assert float(plain_number(value)) == value
