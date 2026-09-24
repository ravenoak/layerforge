from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from layerforge.svg.drawing import StrategyContext


def register_shape_strategies(context: StrategyContext) -> None:
    """Register all shape drawing strategies with the given context.

    Parameters
    ----------
    context : StrategyContext
        The context to register the strategies with.

    Returns
    -------
    None
    """
    from layerforge.svg.drawing.strategies.square_strategy import SquareDrawingStrategy
    from layerforge.svg.drawing.strategies.triangle_strategy import TriangleDrawingStrategy
    from layerforge.svg.drawing.strategies.circle_strategy import CircleDrawingStrategy
    from layerforge.svg.drawing.strategies.arrow_strategy import ArrowDrawingStrategy

    context.register_strategy('square', SquareDrawingStrategy())
    context.register_strategy('triangle', TriangleDrawingStrategy())
    context.register_strategy('circle', CircleDrawingStrategy())
    context.register_strategy('arrow', ArrowDrawingStrategy())
