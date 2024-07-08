from abc import ABC, abstractmethod

import trimesh


class MeshLoader(ABC):
    @abstractmethod
    def load_mesh(self, model_file):
        pass


class TrimeshLoader(MeshLoader):
    def load_mesh(self, model_file):
        return trimesh.load_mesh(model_file)
