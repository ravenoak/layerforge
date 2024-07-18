from . import ShapeDrawingStrategy


class StrategyContext:
    def __init__(self):
        self._strategies = {}

    def register_strategy(self, shape_type, strategy: ShapeDrawingStrategy):
        self._strategies[shape_type.lower()] = strategy

    def draw(self, dwg, shape):
        strategy = self._strategies.get(type(shape).__name__.lower())
        if strategy:
            strategy.draw(dwg, shape)
        else:
            raise ValueError(f"No strategy found for shape type: {type(shape).__name__}")
