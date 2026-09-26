"""Units of length (TR-13).

A default that depends on the material or the machine is stated in millimetres and
converted to the unit of the run. A number that a person gives is already in that unit.
"""

from decimal import Decimal

MM_PER_UNIT = {"mm": 1.0, "cm": 10.0, "in": 25.4}


def from_mm(units: str, value: float) -> float:
    """Return ``value`` millimetres as a length in ``units``."""
    return value / MM_PER_UNIT[units]


def plain_number(value: float) -> str:
    """Write a finite ``value`` in positional notation, so ``1e-05`` is ``0.00001``.

    ``str(float)`` uses an exponent below 1e-4 and above 1e16, which a program that reads a
    length may not accept. Nothing is rounded: the digits are those of ``repr(value)``.
    """
    return format(Decimal(repr(value)), "f")
