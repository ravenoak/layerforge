import math

from svgwrite import Drawing

from src.layerforge.domain.shapes import Arrow
from .base_strategy import ShapeDrawingStrategy


class ArrowDrawingStrategy(ShapeDrawingStrategy):
    """Drawing strategy for Arrow shapes."""

    def draw(self, dwg: Drawing, arrow: Arrow):
        """Draws an Arrow shape on the given Drawing object.

        Parameters
        ----------
        dwg : Drawing
            The Drawing object to draw the shape on.
        arrow : Arrow
            The Arrow shape to draw.
        """
        # TODO: Add some of this as attributes to the Arrow class
        angle = 90  # TODO: Determine if a direction should be added to the arrow
        end = (arrow.x + arrow.size * math.cos(angle),
               arrow.y + arrow.size * math.sin(angle))
        # TODO: Get stroke and fill from the shape or config
        dwg.add(dwg.line((arrow.x, arrow.y), end, stroke='black'))
        dwg.add(dwg.polygon(
            [end,
             (end[0] - 10 * math.cos(angle + math.pi / 6), end[1] - 10 * math.sin(angle + math.pi / 6)),
             (end[0] - 10 * math.cos(angle - math.pi / 6),
              end[1] - 10 * math.sin(angle - math.pi / 6))],
            fill='none', stroke='black'))
