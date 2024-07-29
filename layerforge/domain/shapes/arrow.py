from dataclasses import dataclass

from .base_shape import BaseShape


@dataclass
class Arrow(BaseShape):
    """An arrow shape for reference marks."""

    def type(self) -> str:
        """Return the type of the shape. Always 'arrow' for this class.

        Returns
        -------
        str
            The type of the shape. Always 'arrow'.
        """
        return 'arrow'
