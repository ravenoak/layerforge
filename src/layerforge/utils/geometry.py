import shapely
from shapely.geometry import Polygon
from shapely.geometry.base import BaseGeometry


def polygon_parts(geometry: BaseGeometry) -> list[Polygon]:
    """Return every polygon with positive area inside ``geometry``, however deeply nested.

    ``shapely.get_parts`` descends only one level, so a ``GeometryCollection`` holding a
    ``MultiPolygon`` -- a real output of ``shapely.make_valid`` on some self-intersecting
    polygons, alongside the leftover line of the self-intersection -- would otherwise hide
    that ``MultiPolygon``'s own pieces behind a type that fails an ``isinstance(part, Polygon)``
    check. This walks every level and keeps only what has area.
    """
    parts: list[Polygon] = []
    for part in shapely.get_parts(geometry):
        if isinstance(part, Polygon):
            if part.area > 0:
                parts.append(part)
        elif hasattr(part, "geoms"):
            parts.extend(polygon_parts(part))
    return parts


def calculate_distance(x1: float, y1: float, x2: float, y2: float) -> float:
    """Calculate the distance between two points.

    Parameters
    ----------
    x1 : float
        The x-coordinate of the first point.
    y1 : float
        The y-coordinate of the first point.
    x2 : float
        The x-coordinate of the second point.
    y2 : float
        The y-coordinate of the second point.

    Returns
    -------
    float
        The distance between the two points.
    """
    return float(((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5)
