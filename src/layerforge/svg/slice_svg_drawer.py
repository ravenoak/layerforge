import logging

from shapely.geometry import Polygon
from svgwrite import Drawing

from layerforge.domain.shapes.registry import ShapeFactory
from layerforge.models.reference_marks import ReferenceMark
from layerforge.models.slicing import Slice
from layerforge.models.slicing.number import place_number
from layerforge.svg.drawing.strategy_context import StrategyContext
from layerforge.svg.style import SVGStyle
from layerforge.units import plain_number


class SliceSVGDrawer:
    """Draws SVGs for slices.

    The model's y axis points up and SVG's points down, so everything is drawn
    at ``(x, -y)``. Seen in a viewer, the slice then has the same handedness as
    the model seen from above.

    Everything that is cut, the outlines and the marks, gets the cut colour, a hairline stroke
    and no fill (TR-14). The two kinds differ by their ``class``, not by colour. The number of
    a piece is text with the engrave colour and no stroke (TR-11).
    """

    @staticmethod
    def _cut_attribs(style: SVGStyle, kind: str) -> dict[str, str]:
        """Return the attributes of an element that is cut: ``kind`` is ``outline`` or ``mark``."""
        return {
            "stroke": style.cut_color,
            "stroke_width": plain_number(style.hairline_width),
            "fill": "none",
            "class_": kind,
        }

    @staticmethod
    def draw_contour(dwg: Drawing, contour: Polygon, style: SVGStyle | None = None) -> None:
        """Draws a contour: its outer outline and the outline of each hole.

        Parameters
        ----------
        dwg : Drawing
            The SVG drawing.
        contour : Polygon
            The contour to draw.
        style : SVGStyle, optional
            The colours and the stroke. Without it, the default style in millimetres.

        Returns
        -------
        None
        """
        attribs = SliceSVGDrawer._cut_attribs(style or SVGStyle(), "outline")
        for ring in [contour.exterior, *contour.interiors]:
            points = [(x, -y) for x, y in ring.coords]
            dwg.add(dwg.polygon(points, **attribs))

    @staticmethod
    def draw_reference_marks(
        dwg: Drawing,
        ref_marks: list[ReferenceMark],
        shape_context: StrategyContext,
        style: SVGStyle | None = None,
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
        style : SVGStyle, optional
            The colours and the stroke. Without it, the default style in millimetres.

        Returns
        -------
        None
        """
        attribs = SliceSVGDrawer._cut_attribs(style or SVGStyle(), "mark")
        for mark in ref_marks:
            shape_instance = ShapeFactory.get_shape(
                mark.shape,
                mark.x,
                -mark.y,
                size=mark.size,
                angle=-mark.angle,
            )
            shape_context.draw(dwg, shape_instance, **attribs)

    # The baseline of a text is below its middle by about a third of the font size. The tiny
    # profile has no ``dominant-baseline`` to say "middle", so the drawer moves the baseline.
    _BASELINE_SHIFT = 0.35

    @staticmethod
    def draw_slice(
        dwg: Drawing,
        slice_obj: Slice,
        shape_context: StrategyContext,
        *,
        style: SVGStyle | None = None,
    ) -> None:
        """Draws a slice: the outlines, the marks and the number of each piece.

        The number is the slice index. It goes where its box is farthest from every cut
        (:func:`place_number`). When it fits nowhere, it is drawn at the middle of the piece and
        one warning names the slice.

        Parameters
        ----------
        dwg : Drawing
            The SVG drawing.
        slice_obj : Slice
            The slice to draw.
        shape_context : StrategyContext
            The shape drawing context.
        style : SVGStyle, optional
            The colours, the stroke and the number. Without it, the default style in millimetres.

        Returns
        -------
        None
        """
        style = style or SVGStyle()
        for contour in slice_obj.contours:
            SliceSVGDrawer.draw_contour(dwg, contour, style)

        SliceSVGDrawer.draw_reference_marks(dwg, slice_obj.ref_marks, shape_context, style)

        label = str(slice_obj.index)
        misfits = 0
        for contour in slice_obj.contours:
            placement = place_number(
                contour,
                slice_obj.ref_marks,
                digits=len(label),
                height=style.number_height,
                width_factor=style.number_width_factor,
                clearance=style.number_clearance,
            )
            misfits += not placement.fits
            dwg.add(
                dwg.text(
                    label,
                    insert=(
                        placement.x,
                        -placement.y + SliceSVGDrawer._BASELINE_SHIFT * style.number_height,
                    ),
                    text_anchor="middle",
                    fill=style.engrave_color,
                    font_size=plain_number(style.number_height),
                    font_family="sans-serif",
                    font_weight="bold",
                )
            )
        if misfits:
            logging.warning(
                f"The number of slice {slice_obj.index} does not fit clear of the cuts in "
                f"{misfits} of {len(slice_obj.contours)} pieces. Try a smaller --number-height."
            )
