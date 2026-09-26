from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

# The default snapping radius is this fraction of the mark size (TR-10). TR-16 has no key for it.
TOLERANCE_FACTOR = 0.1


def require(value: float | None, name: str) -> float:
    """Return ``value``, or raise if the config was not resolved (see ``resolved``)."""
    if value is None:
        raise ValueError(f"{name} is not set. Resolve the config with the layer height first.")
    return value


class ReferenceMarkConfig(BaseModel):
    """Configuration options for reference marks.

    ``size``, ``min_distance`` and ``tolerance`` are ``None`` until they are set or derived
    from the sheet (TR-6, TR-10). :meth:`resolved` derives them.
    """

    tolerance: float | None = Field(default=None, allow_inf_nan=False)
    min_distance: float | None = Field(default=None, allow_inf_nan=False)
    available_shapes: list[str] = Field(
        default_factory=lambda: ["circle", "square", "triangle", "arrow"]
    )
    angle: float = Field(default=0.0, allow_inf_nan=False)
    size: float | None = Field(default=None, gt=0, allow_inf_nan=False)
    color: str | None = None
    min_web_ratio: float = Field(default=0.5, ge=0, allow_inf_nan=False)
    kerf: float = Field(default=0.3, ge=0, allow_inf_nan=False)
    min_hole_ratio: float = Field(default=1.0, gt=0, allow_inf_nan=False)
    min_hole_kerf_factor: float = Field(default=1.5, ge=0, allow_inf_nan=False)

    @field_validator("available_shapes")
    @classmethod
    def _validate_shapes(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("available_shapes must not be empty")
        return v

    @field_validator("tolerance", "min_distance")
    @classmethod
    def _non_negative(cls, v: float | None) -> float | None:
        if v is not None and v < 0:
            raise ValueError("values must be non-negative")
        return v

    def min_size(self, layer_height: float) -> float:
        """Return the least hole size that TR-6 asks for on a sheet of ``layer_height``.

        It is the larger of ``min_hole_ratio`` times the sheet thickness and
        ``min_hole_kerf_factor`` times the kerf.
        """
        return max(self.min_hole_ratio * layer_height, self.min_hole_kerf_factor * self.kerf)

    def resolved(self, layer_height: float) -> ReferenceMarkConfig:
        """Return a copy with ``size``, ``min_distance`` and ``tolerance`` all set (TR-6, TR-10).

        A value that is set stays. An unset size is :meth:`min_size`. An unset ``min_distance``
        is the size, and an unset ``tolerance`` is ``TOLERANCE_FACTOR`` times the size. Resolving
        a resolved config changes nothing.
        """
        size = self.size if self.size is not None else self.min_size(layer_height)
        return self.model_copy(
            update={
                "size": size,
                "min_distance": self.min_distance if self.min_distance is not None else size,
                "tolerance": self.tolerance
                if self.tolerance is not None
                else TOLERANCE_FACTOR * size,
            }
        )
