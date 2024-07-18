from layerforge.svg.drawing import ShapeDrawingStrategy
from layerforge.domain.shapes import Triangle


class TriangleDrawingStrategy(ShapeDrawingStrategy):
    def draw(self, dwg, triangle: Triangle):
        dwg.add(dwg.polygon(triangle.vertices, stroke='green', fill='none'))
