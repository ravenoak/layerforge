from dataclasses import dataclass, field
from typing import List

@dataclass
class ReferenceMarkConfig:
    """Configuration options for reference marks."""

    tolerance: float = 10.0
    min_distance: float = 10.0
    available_shapes: List[str] = field(
        default_factory=lambda: ["circle", "square", "triangle", "arrow"]
    )
