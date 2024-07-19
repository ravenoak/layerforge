from layerforge.svg.drawing import ShapeDrawingStrategy
from layerforge.domain.shapes import Circle


class CircleDrawingStrategy(ShapeDrawingStrategy):
    def draw(self, dwg, circle: Circle):
        dwg.add(dwg.circle(center=(circle.x, circle.y), r=circle.radius, stroke='red', fill='none'))
