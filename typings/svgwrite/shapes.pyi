from collections.abc import Sequence
from typing import Any

from .base import BaseElement

Point = tuple[float, float]

class _Transform(BaseElement):
    def rotate(self, angle: float, center: Point | None = ...) -> None: ...

class Line(_Transform):
    def __init__(self, start: Point = ..., end: Point = ..., **extra: Any) -> None: ...

class Rect(_Transform):
    def __init__(
        self,
        insert: Point = ...,
        size: tuple[float, float] = ...,
        rx: float | None = ...,
        ry: float | None = ...,
        **extra: Any,
    ) -> None: ...

class Circle(_Transform):
    def __init__(self, center: Point = ..., r: float = ..., **extra: Any) -> None: ...

class Polyline(_Transform):
    def __init__(self, points: Sequence[Point] = ..., **extra: Any) -> None: ...

class Polygon(Polyline): ...
