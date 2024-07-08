from shapely.geometry import Polygon


class ReferenceMarkCalculator:
    """Class to calculate reference marks for a slice.

    Reference marks are calculated based on the centroids of the polygons in the slice.

    Pseudocode:
    """

    @staticmethod
    def calculate_reference_marks(slice_, mark_manager):
        current_marks = ReferenceMarkCalculator.get_potential_marks(slice_)
        aligned_marks = []

        for centroid in current_marks:
            x, y = centroid
            closest_mark = mark_manager.find_closest_mark(x, y)

            if closest_mark:
                # Directly inherit the shape and size from the closest mark
                mark_tuple = closest_mark
            else:
                # Assign a new mark with a unique shape and default size
                mark_tuple = ReferenceMarkCalculator.assign_new_mark(x, y, mark_manager)

            aligned_marks.append(mark_tuple)

        return aligned_marks

    @staticmethod
    def get_potential_marks(slice_):
        potential_marks = []
        for poly in slice_.contours:
            if isinstance(poly, Polygon):
                centroid = poly.centroid
                potential_marks.append((centroid.x, centroid.y))
        return potential_marks

    @staticmethod
    def assign_new_mark(x, y, mark_manager):
        shape_options = ['circle', 'square', 'triangle']
        size = 5  # Default size
        for shape in shape_options:
            if not any(mark["shape"] == shape for mark in mark_manager.marks.values()):
                mark_manager.add_or_update_mark(x, y, shape, size)
                return x, y, shape, size
        # If all shapes are used, default to 'circle'
        default_shape = 'circle'
        mark_manager.add_or_update_mark(x, y, default_shape, size)
        return x, y, default_shape, size
