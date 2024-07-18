from .model import Model


class ModelFactory:
    def __init__(self, mesh_loader):
        self.mesh_loader = mesh_loader

    def create_model(self, model_file, layer_height, scale_factor=None, target_height=None):
        mesh = self.mesh_loader.load_mesh(model_file)
        mesh = self.scale_mesh(mesh, scale_factor, target_height)
        origin = self.calculate_origin(mesh)
        return Model(mesh, layer_height, origin)

    def scale_mesh(self, mesh, scale_factor=None, target_height=None):
        if scale_factor and target_height:
            raise ValueError("Only one of scale_factor or target_height can be provided.")
        if scale_factor:
            mesh.apply_scale(scale_factor)
        elif target_height:
            current_height = mesh.bounds[1][2] - mesh.bounds[0][2]
            scale_factor = target_height / current_height
            mesh.apply_scale(scale_factor)
        return mesh

    def calculate_origin(self, mesh):
        bounds = mesh.bounds
        return (bounds[0][0] + bounds[1][0]) / 2, (bounds[0][1] + bounds[1][1]) / 2
