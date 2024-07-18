from dataclasses import dataclass

from .base_shape import BaseShape


@dataclass
class Arrow(BaseShape):

    def type(self):
        return 'arrow'
