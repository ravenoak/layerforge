from shapely.geometry import Polygon
from svgwrite import Drawing

from src.layerforge.models.slicing import Slice
from src.layerforge.svg.drawing.shape_factory import ShapeFactory
from src.layerforge.svg.drawing.strategy_context import StrategyContext


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
    def draw_reference_marks(dwg: Drawing, ref_marks: list, shape_context: StrategyContext) -> None:
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
            shape_instance = ShapeFactory.get_shape(mark[2], *mark[:2], size=mark[3])
            if shape_instance:
                shape_context.draw(dwg, shape_instance)

    @staticmethod
    def draw_slice(dwg: Drawing, slice_obj: Slice, shape_context: StrategyContext) -> None:
        """Draws a slice.

        Parameters
        ----------
        dwg : Drawing
            The SVG drawing.
        slice_obj : Slice
            The slice to draw.
        shape_context : StrategyContext
            The shape drawing context.

        Returns
        -------
        None
        """
        for contour in slice_obj.contours:
            SliceSVGDrawer.draw_contour(dwg, contour)

        SliceSVGDrawer.draw_reference_marks(dwg, slice_obj.ref_marks, shape_context)

        # TODO: Ensure text is inside the individual slice
        dwg.add(dwg.text(f"Slice {slice_obj.index}", insert=(10, 20), fill='black'))
