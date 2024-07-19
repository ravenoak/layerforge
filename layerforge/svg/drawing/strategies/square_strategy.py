from layerforge.svg.drawing import ShapeDrawingStrategy
from layerforge.domain.shapes import Square


class SquareDrawingStrategy(ShapeDrawingStrategy):
    def draw(self, dwg, square: Square):
        dwg.add(dwg.rect(insert=(square.x - square.size / 2, square.y - square.size / 2),
                         size=(square.size, square.size), stroke='blue', fill='none'))
