from abc import ABC, abstractmethod

from layerforge.utils.file_operations import ensure_directory_exists, generate_file_name


class SVGWriter(ABC):
    @abstractmethod
    def write(self, svg, output_folder, index):
        pass


class SVGFileWriter(SVGWriter):
    def write(self, svg, output_folder, index):
        ensure_directory_exists(output_folder)
        svg_file = generate_file_name(output_folder, index, 'svg')
        svg.saveas(svg_file)
