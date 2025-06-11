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
