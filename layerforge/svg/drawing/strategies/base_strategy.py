from abc import ABC, abstractmethod


class ShapeDrawingStrategy(ABC):
    @abstractmethod
    def draw(self, dwg, shape):
        pass
