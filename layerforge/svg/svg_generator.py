import svgwrite

from layerforge.svg.slice_svg_drawer import SliceSVGDrawer


class SVGGenerator:
    def __init__(self, output_folder, svg_writer):
        self.output_folder = output_folder
        self.svg_writer = svg_writer

    def generate_svgs(self, slices):
        for slice_obj in slices:
            dwg = svgwrite.Drawing(profile='tiny')
            SliceSVGDrawer.draw_slice(dwg, slice_obj)
            self.svg_writer.write(dwg, self.output_folder, slice_obj.index)