from dataclasses import dataclass

from .base_shape import BaseShape


@dataclass
class Triangle(BaseShape):
    """A triangle shape for reference marks."""

    def type(self) -> str:
        """Return the type of shape. Always 'triangle' for this class.

        Returns
        -------
        str
            The type of shape. Always 'triangle'.
        """
        return 'triangle'

    @property
    def vertices(self) -> list:
        """Return the vertices of the triangle.

        Returns
        -------
        list
            The vertices of the triangle.
        """
        return [(self.x, self.y - self.size),
                (self.x - self.size, self.y + self.size),
                (self.x + self.size, self.y + self.size)]
