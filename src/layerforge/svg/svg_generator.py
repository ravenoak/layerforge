import svgwrite

from layerforge.models.slicing import Slice
from layerforge.svg.drawing import StrategyContext
from layerforge.svg.slice_svg_drawer import SliceSVGDrawer
from layerforge.writers.svg_writer import SVGWriter


class SVGGenerator:
    """Generates SVGs for slices.

    Attributes
    ----------
    output_folder : str
        The folder to output the SVGs to.
    svg_writer : SVGWriter
        The SVG writer to use.
    shape_context : StrategyContext
        The shape strategy context to use.
    units : str
        The unit of the model's numbers: ``mm``, ``cm`` or ``in``. It is the unit of
        the ``width`` and ``height`` of every SVG.
    """

    def __init__(
        self,
        output_folder: str,
        svg_writer: SVGWriter,
        shape_context: StrategyContext,
        units: str = "mm",
    ):
        """Initializes the SVG generator.

        Parameters
        ----------
        output_folder : str
            The folder to output the SVGs to.
        svg_writer : SVGWriter
            The SVG writer to use.
        shape_context : StrategyContext
            The shape strategy context to use.
        units : str
            The unit of the model's numbers, used for the size of every SVG.
        """
        self.output_folder = output_folder
        self.svg_writer = svg_writer
        self.shape_context = shape_context
        self.units = units

    def generate_svgs(self, slices: list[Slice]) -> None:
        """Generates SVGs for slices.

        Parameters
        ----------
        slices : List[Slice]
            The slices to generate SVGs for.

        Returns
        -------
        None
        """
        view_box = self._view_box(slices)
        for slice_obj in slices:
            if view_box is None:
                dwg = svgwrite.Drawing(profile="tiny")
            else:
                x, y, width, height = view_box
                # The size is the view box size in the unit, as text: the tiny profile
                # rounds a float attribute, so a number would differ from the view box.
                size = (f"{width}{self.units}", f"{height}{self.units}")
                dwg = svgwrite.Drawing(profile="tiny", size=size)
                dwg.viewbox(x, y, width, height)
                # The default 16 unit text and 1 unit lines would swamp a model
                # that is a few units across, so scale them with the model.
                extent = max(width, height)
                dwg.attribs["font-size"] = extent / 20
                dwg.attribs["stroke-width"] = extent / 200
            SliceSVGDrawer.draw_slice(dwg, slice_obj, self.shape_context)
            self.svg_writer.write(dwg, self.output_folder, slice_obj.index)

    @staticmethod
    def _view_box(slices: list[Slice]) -> tuple[float, float, float, float] | None:
        """Return one viewBox that holds every contour of every slice.

        The box is in drawing coordinates (y negated, see
        :class:`SliceSVGDrawer`) with a margin of 5% of the larger side.
        Returns ``None`` when no slice has a contour.
        """
        bounds = [c.bounds for s in slices for c in s.contours]
        if not bounds:
            return None
        min_x = min(b[0] for b in bounds)
        max_x = max(b[2] for b in bounds)
        min_y = min(b[1] for b in bounds)
        max_y = max(b[3] for b in bounds)
        margin = 0.05 * (max(max_x - min_x, max_y - min_y) or 1.0)
        return (
            min_x - margin,
            -max_y - margin,
            max_x - min_x + 2 * margin,
            max_y - min_y + 2 * margin,
        )
