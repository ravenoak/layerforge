from dataclasses import dataclass

@dataclass
class ReferenceMark:
    """Represents a reference mark on a slice."""

    x: float
    y: float
    shape: str
    size: float
    angle: float = 0.0
    color: str | None = None
