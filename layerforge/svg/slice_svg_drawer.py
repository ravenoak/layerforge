import numpy as np
from shapely.geometry import Polygon

from layerforge.svg.drawing.shape_factory import ShapeFactory


class SliceSVGDrawer:

    @staticmethod
    def draw_contour(dwg, contour):
        if isinstance(contour, Polygon):
            points = [(x, y) for x, y in contour.exterior.coords]
            dwg.add(dwg.polygon(points, fill='none', stroke='black'))
        elif isinstance(contour, np.ndarray):
            points = [(point[0], point[1]) for point in contour]
            dwg.add(dwg.polygon(points, fill='none', stroke='black'))

    @staticmethod
    def draw_reference_marks(dwg, ref_marks, shape_context):
        for mark in ref_marks:
            shape_instance = ShapeFactory.get_shape(mark[2], *mark[:2], size=mark[3])
            if shape_instance:
                shape_context.draw(dwg, shape_instance)

    @staticmethod
    def draw_slice(dwg, slice_obj, shape_context):
        for contour in slice_obj.contours:
            SliceSVGDrawer.draw_contour(dwg, contour)

        SliceSVGDrawer.draw_reference_marks(dwg, slice_obj.ref_marks, shape_context)

        # TODO: Ensure text is inside the individual slice
        dwg.add(dwg.text(f"Slice {slice_obj.index}", insert=(10, 20), fill='black'))
