from __future__ import annotations

from typing import Any, cast

from svgwrite import Drawing

from layerforge.domain.shapes.base_shape import BaseShape

from .strategies.base_strategy import ShapeDrawingStrategy


class StrategyContext:
    """Context class for drawing strategies.

    This class is responsible for selecting the correct drawing strategy.

    Attributes
    ----------
    _strategies : dict
        A dictionary of strategies with shape type as key and strategy as value.
    """

    def __init__(self) -> None:
        self._strategies: dict[str, ShapeDrawingStrategy] = {}

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

    def draw(self, dwg: Drawing, shape: BaseShape, **attribs: str) -> None:
        """Draws a shape using the appropriate drawing strategy.

        The strategy makes the element and this method styles it, so the strokes of every
        shape are set in one place.

        Parameters
        ----------
        dwg : Drawing
            The SVG drawing to draw the shape on.
        shape : BaseShape
            The shape to draw.
        **attribs : str
            SVG attributes for the element, for example ``stroke="red"`` or ``class_="mark"``.

        Returns
        -------
        None

        Raises
        ------
        ValueError
            If no strategy is found for the shape type.
        """
        strategy = self._strategies.get(type(shape).__name__.lower())
        if strategy is None:
            raise ValueError(f"No strategy found for shape type: {type(shape).__name__}")
        element = strategy.element(dwg, shape)
        # svgwrite's `update` turns `class_` into `class` and `stroke_width` into `stroke-width`.
        # Pyright cannot see the method (it is there at run time), so it is called through Any.
        cast(Any, element).update(attribs)
        dwg.add(element)
