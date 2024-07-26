from abc import ABC, abstractmethod

from svgwrite import Drawing

from layerforge.utils.file_operations import ensure_directory_exists, generate_file_name




class SVGWriter(ABC):
    """Abstract class for writing SVGs."""

    @abstractmethod
    def write(self, svg: Drawing, output_folder: str, index: int) -> None:
        """Write the SVG.

        Parameters
        ----------
        svg : Drawing
            The SVG drawing to write.
        output_folder : str
            The output folder for the SVG file.
        index : int
            The index of the slice.
        """
        pass


class SVGFileWriter(SVGWriter):
    """Class for writing SVGs to files."""

    def write(self, svg: Drawing, output_folder: str, index: int) -> None:
        """Write the SVG as a file to disk in a folder.

        Parameters
        ----------
        svg : Drawing
            The SVG drawing to write.
        output_folder : str
            The output folder for the SVG file.
        index : int
            The index of the slice.
        """
        ensure_directory_exists(output_folder)
        svg_file = generate_file_name(output_folder, index, 'svg')
        svg.saveas(svg_file)
