import math
from typing import TYPE_CHECKING, TypeAlias

from layerforge.utils.optional_dependencies import require_module

if TYPE_CHECKING:
    from svgwrite import Drawing as SvgDrawing
    Drawing: TypeAlias = SvgDrawing
else:
    Drawing: TypeAlias = require_module("svgwrite", "TriangleDrawingStrategy").Drawing  # type: ignore

from layerforge.domain.shapes import Triangle
from layerforge.domain.shapes.base_shape import BaseShape
from .base_strategy import ShapeDrawingStrategy
from typing import cast


class TriangleDrawingStrategy(ShapeDrawingStrategy):
    """Drawing strategy for Triangle shapes."""

    def draw(self, dwg: Drawing, shape: BaseShape) -> None:
        """Draw a :class:`Triangle` shape on ``dwg``."""
        triangle = cast(Triangle, shape)
        color = triangle.color or 'green'
        verts = triangle.vertices
        if triangle.angle:
            verts = []
            cx, cy = triangle.x, triangle.y
            for x, y in triangle.vertices:
                dx, dy = x - cx, y - cy
                r = math.hypot(dx, dy)
                theta = math.atan2(dy, dx) + triangle.angle
                verts.append((cx + r * math.cos(theta), cy + r * math.sin(theta)))

        dwg.add(dwg.polygon(verts, stroke=color, fill='none'))
