"""Mesh abstractions used by the loaders and slicing logic."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Sequence


class Mesh(ABC):
    """Interface describing the operations required by :class:`Model`."""

    @abstractmethod
    def copy(self) -> "Mesh":
        """Return a copy of the mesh."""

    @abstractmethod
    def apply_scale(self, scale: float) -> None:
        """Scale the mesh in-place."""

    @abstractmethod
    def apply_translation(self, translation: Sequence[float]) -> None:
        """Translate the mesh in-place."""

    @property
    @abstractmethod
    def bounds(self) -> Any:
        """Return the bounding box of the mesh."""

    @property
    @abstractmethod
    def extents(self) -> Any:
        """Return the extents of the mesh."""

    @abstractmethod
    def section(
        self, plane_origin: Sequence[float], plane_normal: Sequence[float]
    ) -> Any:
        """Return a section of the mesh at the given plane."""


@dataclass
class TrimeshMesh(Mesh):
    """Wrapper around a :class:`trimesh.Trimesh` object."""

    geometry: Any

    def copy(self) -> "TrimeshMesh":
        return TrimeshMesh(self.geometry.copy())

    def apply_scale(self, scale: float) -> None:
        self.geometry.apply_scale(scale)

    def apply_translation(self, translation: Sequence[float]) -> None:
        self.geometry.apply_translation(translation)

    @property
    def bounds(self) -> Any:
        return self.geometry.bounds

    @property
    def extents(self) -> Any:
        return self.geometry.extents

    def section(
        self, plane_origin: Sequence[float], plane_normal: Sequence[float]
    ) -> Any:
        return self.geometry.section(
            plane_origin=plane_origin, plane_normal=plane_normal
        )



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
    def bounds(self) -> Any:
        return self.geometry.bounds

    @property
    def extents(self) -> Any:
        return self.geometry.extents

    def section(self, plane_origin: Sequence[float], plane_normal: Sequence[float]) -> Any:
        return self.geometry.section(plane_origin=plane_origin, plane_normal=plane_normal)
