from shapely import Polygon, MultiPolygon

from .reference_mark_calculator import ReferenceMarkCalculator
from .reference_mark_adjuster import ReferenceMarkAdjuster
from .reference_mark_manager import ReferenceMarkManager
from ..util import calculate_distance

import logging

logging.basicConfig(level=logging.DEBUG, filename='layerforge_debug.log')


def ensure_polygon(model_contours):
    try:
        if isinstance(model_contours, Polygon):
            return model_contours
        elif isinstance(model_contours, MultiPolygon):
            largest_polygon = max(model_contours, key=lambda p: p.area)
            return largest_polygon
        elif isinstance(model_contours, (list, tuple)):
            model_contours = [tuple(point) if isinstance(point, list) else point for point in model_contours]
            if all(isinstance(item, (list, tuple)) and len(item) == 2 for item in model_contours):
                return Polygon(model_contours)
        else:
            logging.debug(f"Unhandled model_contours type: {type(model_contours)}, content: {model_contours}")
    except Exception as e:
        logging.error(
            f"Failed to create a Polygon from model_contours: {e}, type: {type(model_contours)}, content: {model_contours}")
        raise ValueError(f"Failed to create a Polygon from model_contours due to: {e}")
    raise ValueError("model_contours must be a Polygon object or a sequence of tuples suitable for Polygon creation.")


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
            # Handle the error as appropriate, e.g., skip this slice's mark adjustment or apply default behavior

    def _select_unique_shape(self):
        available_shapes = ['circle', 'square', 'triangle', 'hexagon']
        used_shapes = {mark['shape'] for mark in self.mark_manager.marks}
        for shape in available_shapes:
            if shape not in used_shapes:
                return shape
        return 'circle'

    def _calculate_mark_size(self, x, y):
        # Calculate distance from the mark to the model's origin
        distance = calculate_distance(x, y, self.origin[0], self.origin[1])

        # Calculate mark size based on distance; this logic may be adjusted based on project specifics
        return max(3, min(distance / 10, 5))


class SlicerService:
    @staticmethod
    def calculate_slice_positions(total_height, layer_height):
        return [i * layer_height for i in range(int(total_height / layer_height) + 1)]

    @staticmethod
    def slice_model(model):
        slice_positions = SlicerService.calculate_slice_positions(model.calculate_height(), model.layer_height)
        slices = []
        mark_manager = ReferenceMarkManager()
        previous_marks = []
        for index, position in enumerate(slice_positions):
            contours = model.calculate_slice_contours(position)
            slice_ = Slice(index=index, position=position, contours=contours, origin=model.origin,
                           mark_manager=mark_manager)
            slice_.process_reference_marks()
            slice_.adjust_marks()
            previous_marks = slice_.ref_marks.copy()
            slices.append(slice_)
        return slices
