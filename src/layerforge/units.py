"""Units of length (TR-13).

A default that depends on the material or the machine is stated in millimetres and
converted to the unit of the run. A number that a person gives is already in that unit.
"""

MM_PER_UNIT = {"mm": 1.0, "cm": 10.0, "in": 25.4}


def from_mm(units: str, value: float) -> float:
    """Return ``value`` millimetres as a length in ``units``."""
    return value / MM_PER_UNIT[units]
