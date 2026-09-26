"""The hole a mark makes, and how big a new mark is."""

from shapely.geometry import Polygon

from layerforge.domain.shapes.registry import ShapeFactory
from layerforge.utils import calculate_distance

from .config import ReferenceMarkConfig
from .reference_mark import ReferenceMark


def mark_footprint(mark: ReferenceMark) -> Polygon:
    """Return the outline of the hole that ``mark`` makes (TR-5, TR-7)."""
    shape = ShapeFactory.get_shape(mark.shape, mark.x, mark.y, mark.size, angle=mark.angle)
    return shape.outline()


def mark_size_at(
    config: ReferenceMarkConfig, origin: tuple[float, float], x: float, y: float
) -> float:
    """Return the size of a new mark at ``(x, y)``.

    A configured ``size`` is used as it is. Otherwise the size follows the distance
    from ``origin``, limited to a range of 3 to 5.
    """
    if config.size is not None:
        return config.size
    distance = calculate_distance(x, y, origin[0], origin[1])
    return max(3, min(int(distance / 10), 5))
