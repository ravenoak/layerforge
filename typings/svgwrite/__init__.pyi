from collections.abc import Sequence
from typing import Any

from . import shapes as shapes
from . import text as text
from .base import BaseElement

_Point = tuple[float, float]
_Text = text.Text

class Drawing(BaseElement):
    def __init__(
        self,
        filename: str = ...,
        size: tuple[str | float, str | float] = ...,
        **extra: Any,
    ) -> None: ...
    def saveas(self, filename: str, pretty: bool = ..., indent: int = ...) -> None: ...
    def circle(self, center: _Point = ..., r: float = ..., **extra: Any) -> shapes.Circle: ...
    def rect(
        self,
        insert: _Point = ...,
        size: tuple[float, float] = ...,
        rx: float | None = ...,
        ry: float | None = ...,
        **extra: Any,
    ) -> shapes.Rect: ...
    def line(self, start: _Point = ..., end: _Point = ..., **extra: Any) -> shapes.Line: ...
    def polygon(self, points: Sequence[_Point] = ..., **extra: Any) -> shapes.Polygon: ...
    def text(self, text: str, insert: _Point | None = ..., **extra: Any) -> _Text: ...
