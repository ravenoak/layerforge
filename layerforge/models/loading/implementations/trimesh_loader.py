import trimesh

from layerforge.models.loading.base import MeshLoader


class TrimeshLoader(MeshLoader):
    def load_mesh(self, model_file):
        return trimesh.load_mesh(model_file)
