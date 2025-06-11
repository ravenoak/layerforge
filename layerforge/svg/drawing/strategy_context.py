from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from svgwrite import Drawing
    from .strategies.base_strategy import ShapeDrawingStrategy
else:
    from layerforge.utils.optional_dependencies import require_module
    Drawing = require_module("svgwrite", "StrategyContext").Drawing  # type: ignore
from layerforge.domain.shapes.base_shape import BaseShape


class StrategyContext:
    """Context class for drawing strategies. This class is responsible for selecting the correct drawing strategy.

    Attributes
    ----------
    _strategies : dict
        A dictionary of strategies with shape type as key and strategy as value.
    """

    def __init__(self):
        self._strategies = {}

    def register_strategy(self, shape_type: str, strategy: ShapeDrawingStrategy) -> None:
        """Registers a drawing strategy for a specific shape type.

        Parameters
        ----------
        shape_type : str
            The type of shape to register the strategy for.
        strategy : ShapeDrawingStrategy
            The drawing strategy to register.

        Returns
        -------
        None
        """
        self._strategies[shape_type.lower()] = strategy

    def draw(self, dwg: Drawing, shape: BaseShape) -> None:
        """Draws a shape using the appropriate drawing strategy.

        Parameters
        ----------
        dwg : Drawing
            The SVG drawing to draw the shape on.
        shape : BaseShape
            The shape to draw.

        Returns
        -------
        None

        Raises
        ------
        ValueError
            If no strategy is found for the shape type.
        """
        strategy = self._strategies.get(type(shape).__name__.lower())
        if strategy:
            strategy.draw(dwg, shape)
        else:
            raise ValueError(f"No strategy found for shape type: {type(shape).__name__}")
