from typing import List, Tuple

from layerforge.utils.optional_dependencies import require_module

Polygon = require_module("shapely.geometry", "Model").Polygon
Trimesh = require_module("trimesh", "Model").Trimesh


class Model:
    """ Model class for 3D models.

    Attributes
    ----------
    mesh : trimesh.base.Geometry
        The 3D mesh of the model.
    layer_height : float
        The height of each layer that is sliced from the model.
    origin : Tuple[float, float]
        The origin of the model.
    """

    def __init__(self, mesh: Trimesh, layer_height: float, origin: tuple):
        """Initialize the Model.

        Parameters
        ----------
        mesh : Trimesh
            The 3D mesh of the model.
        layer_height : float
            The height of each layer that is sliced from the model.
        origin : Tuple[float, float]
            The origin of the model.
        """
        self.mesh = mesh
        self.layer_height = layer_height
        self.origin = origin

    def calculate_height(self) -> float:
        """Calculate the height of the model.

        Returns
        -------
        float
            The height of the model.
        """
        min_bound, max_bound = self.mesh.bounds
        height = max_bound[2] - min_bound[2]
        return height

    def calculate_slice_contours(self, position) -> List[Polygon]:
        """Calculate the slice contours at a given position.

        Parameters
        ----------
        position : float
            The position of the slice.

        Returns
        -------
        List[Polygon]
            The slice contours at the given position.
        """
        plane_normal = [0, 0, 1]
        plane_origin = [0, 0, position]
        layer = self.mesh.section(plane_origin=plane_origin, plane_normal=plane_normal)
        if layer is not None:
            slice_2d, _ = layer.to_planar()
            contours = slice_2d.polygons_closed
            return [Polygon(contour) for contour in contours]
        return []
