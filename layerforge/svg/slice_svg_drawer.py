from typing import TYPE_CHECKING

from layerforge.utils.optional_dependencies import require_module

if TYPE_CHECKING:  # pragma: no cover - for type checking only
    from shapely.geometry import Point as ShpPoint, Polygon as ShpPolygon
    from svgwrite import Drawing as SvgDrawing
    Point = ShpPoint
    Polygon = ShpPolygon
    Drawing = SvgDrawing
else:  # pragma: no cover - lazy imports
    _shapely = require_module("shapely.geometry", "SliceSVGDrawer")
    _svgwrite = require_module("svgwrite", "SliceSVGDrawer")
    Point = _shapely.Point
    Polygon = _shapely.Polygon
    Drawing = _svgwrite.Drawing

from layerforge.models.slicing import Slice
from layerforge.models.reference_marks import ReferenceMark
from layerforge.svg.drawing.shape_factory import ShapeFactory
from layerforge.svg.drawing.strategy_context import StrategyContext


class SliceSVGDrawer:
    """Draws SVGs for slices."""

    @staticmethod
    def draw_contour(dwg: Drawing, contour: Polygon) -> None:
        """Draws a contour.

        Parameters
        ----------
        dwg : Drawing
            The SVG drawing.
        contour : Polygon
            The contour to draw.

        Returns
        -------
        None
        """
        points = [(x, y) for x, y in contour.exterior.coords]
        dwg.add(dwg.polygon(points, fill='none', stroke='black'))

    @staticmethod
    def draw_reference_marks(
        dwg: Drawing, ref_marks: list[ReferenceMark], shape_context: StrategyContext
    ) -> None:
        """Draws reference marks.

        Parameters
        ----------
        dwg : Drawing
            The SVG drawing.
        ref_marks : list
            The reference marks to draw.
        shape_context : StrategyContext
            The shape drawing context.

        Returns
        -------
        None
        """
        for mark in ref_marks:
            shape_instance = ShapeFactory.get_shape(
                mark.shape,
                mark.x,
                mark.y,
                size=mark.size,
                angle=mark.angle,
                color=mark.color,
            )
            shape_context.draw(dwg, shape_instance)

    @staticmethod
    def _label_position(contour: Polygon, padding: tuple[float, float] | float | None) -> tuple[float, float]:
        """Return a label position for ``contour`` respecting ``padding``."""
        try:
            pt = contour.centroid
            x, y = pt.x, pt.y
            if not contour.contains(pt):
                minx, miny, maxx, maxy = contour.bounds
                x = (minx + maxx) / 2
                y = (miny + maxy) / 2
        except Exception:
            x, y = 10, 20

        if padding is not None:
            if isinstance(padding, (list, tuple)):
                x += padding[0]
                y += padding[1]
            else:
                x += padding
                y += padding
        return x, y

    @staticmethod
    def draw_slice(
        dwg: Drawing,
        slice_obj: Slice,
        shape_context: StrategyContext,
        padding: tuple[float, float] | float | None = None,
    ) -> None:
        """Draws a slice.

        Parameters
        ----------
        dwg : Drawing
            The SVG drawing.
        slice_obj : Slice
            The slice to draw.
        shape_context : StrategyContext
            The shape drawing context.
        padding : tuple | float | None, optional
            Extra offset applied to label positions.

        Returns
        -------
        None
        """
        for contour in slice_obj.contours:
            SliceSVGDrawer.draw_contour(dwg, contour)

        SliceSVGDrawer.draw_reference_marks(dwg, slice_obj.ref_marks, shape_context)

        for contour in slice_obj.contours:
            x, y = SliceSVGDrawer._label_position(contour, padding)
            dwg.add(dwg.text(f"Slice {slice_obj.index}", insert=(x, y), fill='black'))
