import math
from typing import TYPE_CHECKING

from layerforge.utils.optional_dependencies import require_module

if TYPE_CHECKING:
    from svgwrite import Drawing
else:
    Drawing = require_module("svgwrite", "ArrowDrawingStrategy").Drawing  # type: ignore

from layerforge.domain.shapes import Arrow
from .base_strategy import ShapeDrawingStrategy


class ArrowDrawingStrategy(ShapeDrawingStrategy):
    """Drawing strategy for Arrow shapes."""

    def draw(self, dwg: Drawing, arrow: Arrow) -> None:
        """Draws an Arrow shape on the given Drawing object.

        Parameters
        ----------
        dwg : Drawing
            The Drawing object to draw the shape on.
        arrow : Arrow
            The Arrow shape to draw.
        """
        angle = arrow.angle
        if abs(angle) > 2 * math.pi:
            angle = math.radians(angle)

        end = (
            arrow.x + arrow.size * math.cos(angle),
            arrow.y + arrow.size * math.sin(angle),
        )

        head = arrow.size * 0.2

        stroke_color = arrow.color or 'black'
        dwg.add(dwg.line((arrow.x, arrow.y), end, stroke=stroke_color))
        dwg.add(
            dwg.polygon(
                [
                    end,
                    (
                        end[0] - head * math.cos(angle + math.pi / 6),
                        end[1] - head * math.sin(angle + math.pi / 6),
                    ),
                    (
                        end[0] - head * math.cos(angle - math.pi / 6),
                        end[1] - head * math.sin(angle - math.pi / 6),
                    ),
                ],
                fill="none",
                stroke=stroke_color,
            )
        )
