from .loading.base import MeshLoader
from .loading.mesh import Mesh
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

    def create_model(
        self,
        model_file: str,
        layer_height: float,
        scale_factor: float | None = None,
        target_height: float | None = None,
    ) -> Model:
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
        if isinstance(mesh, list):
            raise ValueError(
                f"Expected a single mesh from '{model_file}', got {len(mesh)} meshes"
            )
        mesh = ModelFactory._scale_mesh(mesh, scale_factor, target_height)
        origin = ModelFactory._calculate_origin(mesh)
        return Model(mesh, layer_height, origin)

    @staticmethod
    def _scale_mesh(
        mesh: Mesh, scale_factor: float | None = None, target_height: float | None = None
    ) -> Mesh:
        """Scale the mesh based on the scale factor or target height.

        Parameters
        ----------
        mesh : Mesh
            The mesh to scale.
        scale_factor : float, optional
            The scale factor to apply to the mesh.
        target_height : float, optional
            The target height for the mesh.

        Returns
        -------
        Mesh
            The scaled mesh.

        Raises
        ------
        ValueError
            If both scale_factor and target_height are provided.
        """
        if scale_factor is not None and target_height is not None:
            raise ValueError(
                "Only one of scale_factor or target_height can be provided."
            )
        if scale_factor is not None:
            mesh.apply_scale(scale_factor)
        elif target_height is not None:
            current_height = mesh.bounds[1][2] - mesh.bounds[0][2]
            scale_factor = target_height / current_height
            mesh.apply_scale(scale_factor)
        return mesh

    @staticmethod
    def _calculate_origin(mesh: Mesh) -> tuple[float, float]:
        """Calculate the (x,y) origin of the mesh.

        Parameters
        ----------
        mesh : Mesh
            The mesh for which to calculate the origin.

        Returns
        -------
        tuple
            The x,y origin of the mesh.
        """
        bounds = mesh.bounds
        return (bounds[0][0] + bounds[1][0]) / 2, (bounds[0][1] + bounds[1][1]) / 2
