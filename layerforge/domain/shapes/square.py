from dataclasses import dataclass

from .base_shape import BaseShape


@dataclass
class Square(BaseShape):

    def type(self):
        return 'square'
