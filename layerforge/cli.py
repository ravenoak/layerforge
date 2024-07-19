import sys

import click

from layerforge.models import ModelFactory, SlicerService
from layerforge.models.loading import LoaderFactory
from layerforge.svg import SVGGenerator
from layerforge.svg.drawing import StrategyContext
from layerforge.utils import initialize_loaders, register_shape_strategies
from layerforge.writers import SVGFileWriter


def process_model(model, output_folder, shape_context):
    slices = SlicerService.slice_model(model)
    svg_writer = SVGFileWriter()
    svg_generator = SVGGenerator(output_folder, svg_writer, shape_context)
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

    shape_context = StrategyContext()
    register_shape_strategies(shape_context)
    initialize_loaders()
    mesh_loader = LoaderFactory.get_loader("trimesh")
    model_factory = ModelFactory(mesh_loader)
    model = model_factory.create_model(stl_file, layer_height, scale_factor, target_height)

    process_model(model, output_folder, shape_context)


if __name__ == '__main__':
    cli()
