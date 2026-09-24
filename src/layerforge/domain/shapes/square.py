from dataclasses import dataclass

from .base_shape import BaseShape


@dataclass
class Square(BaseShape):
    """A square shape for reference marks."""

    def type(self) -> str:
        """Return the type of shape. Always 'square' for this class.

        Returns
        -------
        str
            The type of shape. Always 'square'.
        """
        return 'square'
