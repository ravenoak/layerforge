from dataclasses import dataclass

from .base_shape import BaseShape


@dataclass
class Circle(BaseShape):

    def type(self):
        return 'circle'

    @property
    def radius(self):
        return self.size / 2
