import sys

import click

from layerforge.models import ModelFactory, TrimeshLoader, SlicerService
from layerforge.svg import SVGGenerator
from layerforge.writers import SVGFileWriter


def process_model(model, output_folder):
    slices = SlicerService.slice_model(model)
    svg_writer = SVGFileWriter()
    svg_generator = SVGGenerator(output_folder, svg_writer)
    svg_generator.generate_svgs(slices)


@click.command()
@click.option('--stl-file', prompt='STL file path', help='The path to the STL file.')
@click.option('--layer-height', default=3.0, help='The layer height.')
@click.option('--output-folder', default='output', help='The output folder for SVG files.')
@click.option('--scale-factor', default=None, type=float, help='The scale factor to apply to the model.')
@click.option('--target-height', default=None, type=float, help='The target height for the model.')
def cli(stl_file, layer_height, output_folder, scale_factor, target_height):
    """This script processes an STL file and generates SVG slices."""
    if scale_factor and target_height:
        print("Only one of scale_factor or target_height can be provided.")
        sys.exit(1)

    mesh_loader = TrimeshLoader()
    model_factory = ModelFactory(mesh_loader)
    model = model_factory.create_model(stl_file, layer_height, scale_factor, target_height)

    process_model(model, output_folder)


if __name__ == '__main__':
    cli()
