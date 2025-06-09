import logging
from typing import List

from shapely.geometry import Polygon

from layerforge.models.reference_marks import (
    ReferenceMark,
    ReferenceMarkAdjuster,
    ReferenceMarkCalculator,
    ReferenceMarkManager,
)
from layerforge.utils import calculate_distance


class Slice:
    """Represents a single slice of a 3D model.

    Attributes
    ----------
    index : int
        The index of the slice in the model.
    position : float
        The Z position of the slice.
    contours : list
        A list of contours in the slice.
    origin : tuple
        The origin of the model.
    ref_marks : List[ReferenceMark]
        A list of reference marks in the slice.
    mark_manager : ReferenceMarkManager
        The reference mark manager for the slice.
    """

    def __init__(self, index: int, position: float, contours: List[Polygon], origin: tuple,
                 mark_manager: ReferenceMarkManager):
        """Initialize the slice.

        Parameters
        ----------
        index : int
            The index of the slice in the model.
        position : float
            The Z position of the slice.
        contours : list
            A list of contours in the slice.
        origin : tuple
            The origin of the model.
        mark_manager : ReferenceMarkManager
            The reference mark manager for the slice.
        """
        self.contours = contours
        self.index = index
        self.mark_manager = mark_manager
        self.origin = origin
        self.position = position

        self.ref_marks: List[ReferenceMark] = []

    def process_reference_marks(self) -> None:
        """Process reference marks for the slice.

        This method calculates potential reference marks, adjusts
        existing marks, and adds new marks. It uses the ReferenceMarkCalculator
        class.

        Returns
        -------
        None
        """
        potential_marks = ReferenceMarkCalculator.get_potential_marks(self)
        for centroid in potential_marks:
            x, y = centroid
            existing_mark = self.mark_manager.find_mark_by_position(x, y)
            if existing_mark:
                self.ref_marks.append(
                    ReferenceMark(x=x, y=y, shape=existing_mark.shape, size=existing_mark.size)
                )
            else:
                new_shape = self._select_unique_shape()
                new_size = self._calculate_mark_size(x, y)
                self.mark_manager.add_or_update_mark(x, y, new_shape, new_size)
                self.ref_marks.append(ReferenceMark(x=x, y=y, shape=new_shape, size=new_size))

    def adjust_marks(self) -> None:
        """Adjust reference marks for the slice.

        This method adjusts reference marks based on the contours
        using the ReferenceMarkAdjuster class.

        Returns
        -------
        None

        Raises
        ------
        ValueError
            If an error occurs in adjusting the marks.
        """
        logging.debug(f"model_contours type: {type(self.contours)}, content: {self.contours}")
        try:
            self.ref_marks = ReferenceMarkAdjuster.adjust_marks(self.ref_marks, self.contours)
        except ValueError as e:
            logging.error(f"Error in adjusting marks for slice {self.index}: {e}")

    def _select_unique_shape(self) -> str:
        """Select a unique shape for a reference mark.

        Returns
        -------
        str
            A unique shape for the reference mark.
        """
        available_shapes = ['circle', 'square', 'triangle', 'arrow']
        used_shapes = {mark.shape for mark in self.mark_manager.marks}
        for shape in available_shapes:
            if shape not in used_shapes:
                return shape
        return 'arrow'

    def _calculate_mark_size(self, x: float, y: float) -> float:
        """Calculate the size of a mark based on distance from origin.

        The sizes are limited to a range of 3 to 5.

        Parameters
        ----------
        x : float
            The x-coordinate of the mark.
        y : float
            The y-coordinate of the mark.

        Returns
        -------
        float
            The size of the mark.
        """
        distance = calculate_distance(x, y, self.origin[0], self.origin[1])
        return max(3, min(int(distance / 10), 5))
