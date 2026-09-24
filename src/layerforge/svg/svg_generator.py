from typing import List

from layerforge.utils.optional_dependencies import require_module

svgwrite = require_module("svgwrite", "SVGGenerator")

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
    """

    def __init__(self, output_folder: str, svg_writer: SVGWriter, shape_context: StrategyContext):
        """Initializes the SVG generator.

        Parameters
        ----------
        output_folder : str
            The folder to output the SVGs to.
        svg_writer : SVGWriter
            The SVG writer to use.
        shape_context : StrategyContext
            The shape strategy context to use.
        """
        self.output_folder = output_folder
        self.svg_writer = svg_writer
        self.shape_context = shape_context

    def generate_svgs(self, slices: List[Slice]) -> None:
        """Generates SVGs for slices.

        Parameters
        ----------
        slices : List[Slice]
            The slices to generate SVGs for.

        Returns
        -------
        None
        """
        for slice_obj in slices:
            dwg = svgwrite.Drawing(profile='tiny')
            SliceSVGDrawer.draw_slice(dwg, slice_obj, self.shape_context)
            self.svg_writer.write(dwg, self.output_folder, slice_obj.index)
