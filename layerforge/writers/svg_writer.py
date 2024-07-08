from abc import ABC, abstractmethod
import pathlib


class SVGWriter(ABC):
    @abstractmethod
    def write(self, svg, output_folder, index):
        pass


class SVGFileWriter(SVGWriter):
    def write(self, svg, output_folder, index):
        self.ensure_output_folder_exists(output_folder)
        svg_file = self.get_svg_file_name(output_folder, index)
        svg.saveas(svg_file)

    @staticmethod
    def ensure_output_folder_exists(output_folder):
        pathlib.Path(output_folder).mkdir(parents=True, exist_ok=True)

    @staticmethod
    def get_svg_file_name(output_folder, index):
        return f"{output_folder}/slice_{index:03d}.svg"
