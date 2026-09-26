from functools import reduce

from shapely.geometry import Polygon

from .loading.mesh import Mesh


class Model:
    """Model class for 3D models.

    Attributes
    ----------
    mesh : Mesh
        The 3D mesh of the model.
    layer_height : float
        The height of each layer that is sliced from the model.
    """

    def __init__(self, mesh: Mesh, layer_height: float):
        """Initialize the Model.

        Parameters
        ----------
        mesh : Mesh
            The 3D mesh of the model.
        layer_height : float
            The height of each layer that is sliced from the model.
        """
        self.mesh = mesh
        self.layer_height = layer_height

    def calculate_slice_contours(self, position: float) -> list[Polygon]:
        """Calculate the slice contours at a given position.

        Parameters
        ----------
        position : float
            The position of the slice.

        Returns
        -------
        List[Polygon]
            The slice contours at the given position, in the model's x and y
            coordinates. A contour with a hole has an interior ring.
        """
        plane_normal = [0, 0, 1]
        plane_origin = [0, 0, position]
        layer = self.mesh.section(plane_origin=plane_origin, plane_normal=plane_normal)
        if layer is not None:
            # Without an explicit transform, trimesh re-centres every cut on its
            # own vertices. This one only drops z, so all slices share the
            # model's x and y.
            to_plane = [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, -position], [0, 0, 0, 1]]
            slice_2d, _ = layer.to_2D(to_2D=to_plane)
            loops = [Polygon(contour) for contour in slice_2d.polygons_closed]
            if not loops:
                return []
            # Every closed loop is a solid polygon on its own. Taking the
            # symmetric difference applies the even-odd rule, so a loop inside
            # another becomes a hole, and a loop inside that a solid again.
            # (trimesh's ``polygons_full`` does this too but needs ``rtree``.)
            merged = reduce(lambda a, b: a.symmetric_difference(b), loops)
            parts = getattr(merged, "geoms", [merged])
            return [part for part in parts if isinstance(part, Polygon) and not part.is_empty]
        return []
