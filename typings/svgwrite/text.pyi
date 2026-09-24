from typing import Any

from .shapes import Point, _Transform

class Text(_Transform):
    def __init__(
        self,
        text: str,
        insert: Point | None = ...,
        x: Any = ...,
        y: Any = ...,
        **extra: Any,
    ) -> None: ...
