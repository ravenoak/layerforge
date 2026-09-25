from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class ReferenceMarkConfig(BaseModel):
    """Configuration options for reference marks."""

    tolerance: float = Field(default=10.0, allow_inf_nan=False)
    min_distance: float = Field(default=10.0, allow_inf_nan=False)
    available_shapes: list[str] = Field(
        default_factory=lambda: ["circle", "square", "triangle", "arrow"]
    )
    angle: float = Field(default=0.0, allow_inf_nan=False)
    size: float | None = Field(default=None, gt=0, allow_inf_nan=False)
    color: str | None = None

    @field_validator("available_shapes")
    @classmethod
    def _validate_shapes(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("available_shapes must not be empty")
        return v

    @field_validator("tolerance", "min_distance")
    @classmethod
    def _non_negative(cls, v: float) -> float:
        if v < 0:
            raise ValueError("values must be non-negative")
        return v
