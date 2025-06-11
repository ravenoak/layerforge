from dataclasses import dataclass
from typing import Any, Sequence


@dataclass
class Mesh:
    """Lightweight wrapper around an underlying mesh implementation."""

    geometry: Any

    def copy(self) -> "Mesh":
        """Return a copy of the mesh."""
        return Mesh(self.geometry.copy())

    def apply_scale(self, scale: float) -> None:
        self.geometry.apply_scale(scale)

    def apply_translation(self, translation: Sequence[float]) -> None:
        self.geometry.apply_translation(translation)

    @property
    def bounds(self):
        return self.geometry.bounds

    @property
    def extents(self):
        return self.geometry.extents

    def section(self, plane_origin, plane_normal):
        return self.geometry.section(plane_origin=plane_origin, plane_normal=plane_normal)
