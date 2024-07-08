from shapely.geometry import Polygon
import numpy as np


class SliceSVGDrawer:
    @staticmethod
    def draw_slice(dwg, slice_obj):
        for contour in slice_obj.contours:
            if isinstance(contour, Polygon):
                points = [(x, y) for x, y in contour.exterior.coords]
                dwg.add(dwg.polygon(points, fill='none', stroke='black'))
            elif isinstance(contour, np.ndarray):
                points = [(point[0], point[1]) for point in contour]
                dwg.add(dwg.polygon(points, fill='none', stroke='black'))

        print(f"Drawing slice {slice_obj.index} with ref_marks: {slice_obj.ref_marks}")
        for mark in slice_obj.ref_marks:
            x, y, shape, size = mark
            if shape == 'circle':
                dwg.add(dwg.circle(center=(x, y), r=size, stroke='red', fill='none'))
            elif shape == 'square':
                dwg.add(dwg.rect(insert=(x - size / 2, y - size / 2), size=(size, size), stroke='blue', fill='none'))
            elif shape == 'triangle':
                points = [(x, y - size), (x - size, y + size), (x + size, y + size)]
                dwg.add(dwg.polygon(points, stroke='green', fill='none'))

        # Add slice number
        dwg.add(dwg.text(f"Slice {slice_obj.index}", insert=(10, 20), fill='black'))
