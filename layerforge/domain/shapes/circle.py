from dataclasses import dataclass

from .base_shape import BaseShape


@dataclass
class Circle(BaseShape):
    """A circle shape for reference marks."""

    def type(self) -> str:
        """Return the type of the shape. Always 'circle' for this class.

        Returns
        -------
        str
            The type of the shape. Always 'circle'.
        """
        return 'circle'

    @property
    def radius(self) -> float:
        """Return the radius of the circle.

        Returns
        -------
        float
            The radius of the circle.
        """
        return self.size / 2
