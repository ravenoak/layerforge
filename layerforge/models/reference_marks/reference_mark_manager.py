from typing import List, Optional

from layerforge.utils import calculate_distance
from .reference_mark import ReferenceMark


class ReferenceMarkManager:
    """Manage reference marks on a slice of a 3D model.

    Attributes
    ----------
    marks : List[ReferenceMark]
        Collected reference marks for the model.
    """

    def __init__(self) -> None:
        self.marks: List[ReferenceMark] = []

    def find_mark_by_position(self, x: float, y: float, tolerance: float = 10) -> Optional[ReferenceMark]:
        """Return the mark at ``(x, y)`` if within ``tolerance`` distance."""
        for mark in self.marks:
            distance = calculate_distance(mark.x, mark.y, x, y)
            if distance <= tolerance:
                return mark
        return None

    def add_or_update_mark(self, x: float, y: float, shape: str, size: float) -> None:
        """Add a new mark or update an existing one."""
        mark = self.find_mark_by_position(x, y)
        if mark:
            mark.shape = shape
            mark.size = size
        else:
            self.marks.append(ReferenceMark(x=x, y=y, shape=shape, size=size))
