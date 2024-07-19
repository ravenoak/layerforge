import math

from layerforge.svg.drawing import ShapeDrawingStrategy
from layerforge.domain.shapes import Arrow


class ArrowDrawingStrategy(ShapeDrawingStrategy):
    def draw(self, dwg, arrow: Arrow):
        angle = 90  # TODO: Determine if a direction should be added to the arrow
        end = (arrow.x + arrow.size * math.cos(angle),
               arrow.y + arrow.size * math.sin(angle))
        dwg.add(dwg.line((arrow.x, arrow.y), end, stroke='black'))
        dwg.add(dwg.polygon(
            [end,
             (end[0] - 10 * math.cos(angle + math.pi / 6), end[1] - 10 * math.sin(angle + math.pi / 6)),
             (end[0] - 10 * math.cos(angle - math.pi / 6),
              end[1] - 10 * math.sin(angle - math.pi / 6))],
            fill='none', stroke='black'))
