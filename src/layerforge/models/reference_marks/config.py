from __future__ import annotations

from typing import List
from pydantic import BaseModel, Field, field_validator


class ReferenceMarkConfig(BaseModel):
    """Configuration options for reference marks."""

    tolerance: float = 10.0
    min_distance: float = 10.0
    available_shapes: List[str] = Field(
        default_factory=lambda: ["circle", "square", "triangle", "arrow"]
    )
    angle: float = 0.0
    color: str | None = None

    @field_validator("available_shapes")
    @classmethod
    def _validate_shapes(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValueError("available_shapes must not be empty")
        return v

    @field_validator("tolerance", "min_distance")
    @classmethod
    def _non_negative(cls, v: float) -> float:
        if v < 0:
            raise ValueError("values must be non-negative")
        return v

