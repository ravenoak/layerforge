from abc import ABC, abstractmethod


class MeshLoader(ABC):
    @abstractmethod
    def load_mesh(self, model_file):
        pass
