from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.layerforge.models.slicing.slice import Slice


class ReferenceMarkCalculator:
    """Class to calculate reference marks for a slice.

    Reference marks are calculated based on the centroids of the polygons in the slice.

    For each polygon in the slice:
        1. Calculate the centroid of the polygon.
        2. Add the centroid to the list of potential marks.
    """

    @staticmethod
    def get_potential_marks(layer: Slice) -> list:
        """Calculate the potential reference marks for a slice.

        Parameters
        ----------
        layer : Slice
            The slice to calculate reference marks for.

        Returns
        -------
        list
            A list of potential reference marks.
        """
        potential_marks = []
        for poly in layer.contours:
            centroid = poly.centroid
            potential_marks.append((centroid.x, centroid.y))
        return potential_marks
