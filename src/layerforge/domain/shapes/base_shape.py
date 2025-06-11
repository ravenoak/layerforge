from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class BaseShape(ABC):
    """A base class for reference mark shapes.

    Attributes
    ----------
    x : float
        The x-coordinate of the center of the shape.
    y : float
        The y-coordinate of the center of the shape.
    size : float
        The size of the shape.
    """
    x: float
    y: float
    size: float

    @abstractmethod
    def type(self) -> str:
        """Return the type of the shape.

        Returns
        -------
        str
            The type of the shape.
        """
        pass
