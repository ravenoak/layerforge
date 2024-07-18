from dataclasses import dataclass

from .base_shape import BaseShape


@dataclass
class Triangle(BaseShape):

    def type(self):
        return 'triangle'

    @property
    def vertices(self):
        return [(self.x, self.y - self.size),
                (self.x - self.size, self.y + self.size),
                (self.x + self.size, self.y + self.size)]
