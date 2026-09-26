from shapely.geometry import Point, Polygon
from svgwrite import Drawing

from layerforge.domain.shapes.registry import ShapeFactory
from layerforge.models.reference_marks import ReferenceMark
from layerforge.models.slicing import Slice
from layerforge.svg.drawing.strategy_context import StrategyContext


class SliceSVGDrawer:
    """Draws SVGs for slices.

    The model's y axis points up and SVG's points down, so everything is drawn
    at ``(x, -y)``. Seen in a viewer, the slice then has the same handedness as
    the model seen from above.
    """

    @staticmethod
    def draw_contour(dwg: Drawing, contour: Polygon) -> None:
        """Draws a contour: its outer outline and the outline of each hole.

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
        for ring in [contour.exterior, *contour.interiors]:
            points = [(x, -y) for x, y in ring.coords]
            dwg.add(dwg.polygon(points, fill="none", stroke="black"))

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
                -mark.y,
                size=mark.size,
                angle=-mark.angle,
                color=mark.color,
            )
            shape_context.draw(dwg, shape_instance)

    @staticmethod
    def _label_position(
        contour: Polygon, padding: tuple[float, float] | float | None
    ) -> tuple[float, float]:
        """Return a label position for ``contour`` respecting ``padding``."""
        try:
            pt = contour.centroid
            if not contour.contains(pt):
                minx, miny, maxx, maxy = contour.bounds
                pt = Point((minx + maxx) / 2, (miny + maxy) / 2)
            if not contour.contains(pt):
                pt = contour.representative_point()
            x, y = pt.x, pt.y
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
            Extra offset applied to label positions, in model coordinates.

        Returns
        -------
        None
        """
        for contour in slice_obj.contours:
            SliceSVGDrawer.draw_contour(dwg, contour)

        SliceSVGDrawer.draw_reference_marks(dwg, slice_obj.ref_marks, shape_context)

        for contour in slice_obj.contours:
            x, y = SliceSVGDrawer._label_position(contour, padding)
            dwg.add(dwg.text(f"Slice {slice_obj.index}", insert=(x, -y), fill="black"))
