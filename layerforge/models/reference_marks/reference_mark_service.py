from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - for type checking only
    from layerforge.models.slicing.slice import Slice


class ReferenceMarkService:
    """Utility service for processing reference marks on a slice."""

    @staticmethod
    def process_slice(slice_: "Slice") -> None:
        """Calculate and adjust reference marks for ``slice_``."""
        slice_.process_reference_marks()
        slice_.adjust_marks()

