from trimesh import Trimesh

from .loading.base import MeshLoader
from .model import Model


class ModelFactory:
    """Factory class for creating Model objects.

    Attributes
    ----------
    mesh_loader : MeshLoader
        The mesh loader to use for loading the model file.
    """

    def __init__(self, mesh_loader: MeshLoader):
        """Initialize the ModelFactory.

        Parameters
        ----------
        mesh_loader : MeshLoader
            The mesh loader to use for loading the model file.
        """
        self.mesh_loader = mesh_loader

    def create_model(self, model_file: str, layer_height: float, scale_factor: float = None,
                     target_height: float = None) -> Model:
        """Create a Model object from an STL file.

        Parameters
        ----------
        model_file : str
            The path to the STL file.
        layer_height : float
            The height of each layer that is sliced from the model.
        scale_factor : float, optional
            The scale factor to apply to the model.
        target_height : float, optional
            The target height for the model.

        Returns
        -------
        Model
            The Model object created from the STL file.
        """
        mesh = self.mesh_loader.load_mesh(model_file)
        # TODO: Add a check for List[Trimesh]/List[Geometry] and throw an error if it is not a single mesh.
        mesh = self._scale_mesh(mesh, scale_factor, target_height)
        origin = self._calculate_origin(mesh)
        return Model(mesh, layer_height, origin)

    # TODO: Investigate if _scale_mesh needs to be converted to a static method or the class refactored.
    def _scale_mesh(self, mesh: Trimesh, scale_factor: float = None, target_height: float = None) -> Trimesh:
        """Scale the mesh based on the scale factor or target height.

        Parameters
        ----------
        mesh : Trimesh
            The mesh to scale.
        scale_factor : float, optional
            The scale factor to apply to the mesh.
        target_height : float, optional
            The target height for the mesh.

        Returns
        -------
        Trimesh
            The scaled mesh.

        Raises
        ------
        ValueError
            If both scale_factor and target_height are provided.
        """
        if scale_factor and target_height:
            raise ValueError("Only one of scale_factor or target_height can be provided.")
        if scale_factor:
            mesh.apply_scale(scale_factor)
        elif target_height:
            current_height = mesh.bounds[1][2] - mesh.bounds[0][2]
            scale_factor = target_height / current_height
            mesh.apply_scale(scale_factor)
        return mesh

    # TODO: Investigate if _calculate_origin needs to be converted to a static method or the class refactored.
    def _calculate_origin(self, mesh: Trimesh) -> tuple:
        """Calculate the (x,y) origin of the mesh.

        Parameters
        ----------
        mesh : Trimesh
            The mesh for which to calculate the origin.

        Returns
        -------
        tuple
            The x,y origin of the mesh.
        """
        bounds = mesh.bounds
        return (bounds[0][0] + bounds[1][0]) / 2, (bounds[0][1] + bounds[1][1]) / 2
