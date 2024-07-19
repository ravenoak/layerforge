from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class BaseShape(ABC):
    x: float
    y: float
    size: float

    @abstractmethod
    def type(self):
        pass
