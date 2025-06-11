from typing import List, TYPE_CHECKING

from layerforge.utils.optional_dependencies import require_module

if TYPE_CHECKING:  # pragma: no cover
    from shapely.geometry import Polygon as ShpPolygon
    Polygon = ShpPolygon
else:
    Polygon = require_module("shapely.geometry", "Model").Polygon
from .loading.mesh import Mesh


class Model:
    """ Model class for 3D models.

    Attributes
    ----------
    mesh : Mesh
        The 3D mesh of the model.
    layer_height : float
        The height of each layer that is sliced from the model.
    origin : Tuple[float, float]
        The origin of the model.
    """

    def __init__(self, mesh: Mesh, layer_height: float, origin: tuple[float, float]):
        """Initialize the Model.

        Parameters
        ----------
        mesh : Mesh
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

    def calculate_slice_contours(self, position: float) -> list[Polygon]:
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
        layer = self.mesh.section(
            plane_origin=plane_origin, plane_normal=plane_normal
        )
        if layer is not None:
            if hasattr(layer, "to_2D"):
                slice_2d = layer.to_2D()
            else:
                slice_2d, _ = layer.to_planar()
            contours = slice_2d.polygons_closed
            return [Polygon(contour) for contour in contours]
        return []
