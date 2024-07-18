import logging

from layerforge.models.reference_marks import ReferenceMarkAdjuster
from layerforge.models.reference_marks import ReferenceMarkCalculator
from layerforge.utils import calculate_distance, ensure_polygon


class Slice:
    def __init__(self, index, position, contours, origin, mark_manager):
        self.index = index
        self.position = position
        self.contours = contours
        self.origin = origin
        self.ref_marks = []
        self.mark_manager = mark_manager

    def process_reference_marks(self):
        potential_marks = ReferenceMarkCalculator.get_potential_marks(self)
        for centroid in potential_marks:
            x, y = centroid
            existing_mark = self.mark_manager.find_mark_by_position(x, y)
            if existing_mark:
                self.ref_marks.append((x, y, existing_mark['shape'], existing_mark['size']))
            else:
                new_shape = self._select_unique_shape()
                new_size = self._calculate_mark_size(x, y)
                self.mark_manager.add_or_update_mark(x, y, new_shape, new_size)
                self.ref_marks.append((x, y, new_shape, new_size))

    def adjust_marks(self):
        logging.debug(f"model_contours type: {type(self.contours)}, content: {self.contours}")
        try:
            model_polygon = ensure_polygon(self.contours)
            self.ref_marks = ReferenceMarkAdjuster.adjust_marks(self.ref_marks, model_polygon)
        except ValueError as e:
            logging.error(f"Error in adjusting marks for slice {self.index}: {e}")

    def _select_unique_shape(self):
        available_shapes = ['circle', 'square', 'triangle', 'arrow']
        used_shapes = {mark['shape'] for mark in self.mark_manager.marks}
        for shape in available_shapes:
            if shape not in used_shapes:
                return shape
        return 'arrow'

    def _calculate_mark_size(self, x, y):
        # Calculate distance from the mark to the model's origin
        distance = calculate_distance(x, y, self.origin[0], self.origin[1])

        # Calculate mark size based on distance; this logic may be adjusted based on project specifics
        return max(3, min(distance / 10, 5))
