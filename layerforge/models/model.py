from .slice import Slice
from ..writers.svg_writer import SVGFileWriter


class Model:
    def __init__(self, mesh, layer_height, origin):
        self.mesh = mesh
        self.layer_height = layer_height
        self.origin = origin

    def calculate_height(self):
        # Get the bounding box of the model
        min_bound, max_bound = self.mesh.bounds
        # Calculate the height as the difference in the Z dimension
        height = max_bound[2] - min_bound[2]
        return height

    def calculate_slice_contours(self, position):
        # Define the slicing plane
        plane_normal = [0, 0, 1]  # Z-axis
        plane_origin = [0, 0, position]  # Position on Z-axis
        # Slice the mesh
        slice_ = self.mesh.section(plane_origin=plane_origin, plane_normal=plane_normal)
        # Get the polyline from the slice
        if slice_ is not None:
            slice_2D, to_3D = slice_.to_planar()
            contours = slice_2D.polygons_closed
            return contours
        return []
