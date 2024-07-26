from layerforge.utils import calculate_distance


class ReferenceMarkManager:
    """Manages reference marks on a slice of a 3D model.

    Attributes
    ----------
    marks : list
        A list of reference marks. Each mark is a dict with keys: x, y, shape, size
    """

    def __init__(self):
        self.marks = []

    def find_mark_by_position(self, x: float, y: float, tolerance: float = 10) -> dict or None:
        """Accept a mark by its position if within tolerance.

        Parameters
        ----------
        x : float
            The x-coordinate of the mark.
        y : float
            The y-coordinate of the mark.
        tolerance : float, optional
            The maximum distance between the mark and the given position.

        Returns
        -------
        dict or None
            The mark if found within tolerance, otherwise None.
        """
        for mark in self.marks:
            distance = calculate_distance(mark['x'], mark['y'], x, y)
            if distance <= tolerance:
                return mark
        return None

    def add_or_update_mark(self, x: float, y: float, shape: str, size: float) -> None:
        """Add or update a reference mark at the given position.

        The mark is updated if it already exists within tolerance.

        Parameters
        ----------
        x : float
            The x-coordinate of the mark.
        y : float
            The y-coordinate of the mark.
        shape : str
            The shape of the mark.
        size : float
            The size of the mark.

        Returns
        -------
        None
        """
        mark = self.find_mark_by_position(x, y)
        if mark:
            mark['shape'] = shape
            mark['size'] = size
        else:
            self.marks.append({'x': x, 'y': y, 'shape': shape, 'size': size})
