import sys

import click

from layerforge.models import Model, ModelFactory, SlicerService
from layerforge.models.reference_marks import ReferenceMarkConfig
from layerforge.models.loading import LoaderFactory
from layerforge.svg import SVGGenerator
from layerforge.svg.drawing import StrategyContext
from layerforge.utils import initialize_loaders, register_shape_strategies
from layerforge.writers import SVGFileWriter


def process_model(
    model: Model,
    output_folder: str,
    shape_context: StrategyContext,
    config: ReferenceMarkConfig,
) -> None:
    """Process the model and generate SVG slices.

    Parameters
    ----------
    model : Model
        The model to process.
    output_folder : str
        The output folder for SVG files.
    shape_context : StrategyContext
        The context for the shape strategies.

    Returns
    -------
    None
    """
    # TODO: Refactor this to either include the rest of the logic that is in the CLI function, or completely rewrite it.
    slices = SlicerService.slice_model(model, config=config)
    svg_writer = SVGFileWriter()
    svg_generator = SVGGenerator(output_folder, svg_writer, shape_context)
    svg_generator.generate_svgs(slices)


@click.command()
@click.option('--stl-file', prompt='STL file path', help='The path to the STL file.')
@click.option('--layer-height', default=3.0, help='The layer height.')
@click.option('--output-folder', default='output', help='The output folder for SVG files.')
@click.option('--scale-factor', default=None, type=float, help='The scale factor to apply to the model.')
@click.option('--target-height', default=None, type=float, help='The target height for the model.')
@click.option('--mark-tolerance', default=10.0, type=float, help='Tolerance when matching existing marks.')
@click.option('--mark-min-distance', default=10.0, type=float, help='Minimum distance from contours and between marks.')
@click.option('--available-shapes', default='circle,square,triangle,arrow', help='Comma separated list of mark shapes.')
def cli(
    stl_file: str,
    layer_height: float,
    output_folder: str,
    scale_factor: float,
    target_height: float,
    mark_tolerance: float,
    mark_min_distance: float,
    available_shapes: str,
) -> None:
    """Entry point for the CLI.

    This function wraps all the logic for processing an STL file and
    generating SVG slices while accepting commandline arguments.

    Parameters
    ----------
    stl_file : str
        The path to the STL file.
    layer_height : float
        The height of each layer that is sliced from the model.
    output_folder : str
        The output folder for slice files in SVG format.
    scale_factor : float, optional
        The scale factor to apply to the model before slicing.
    target_height : float, optional
        The target height for the model before slicing.

    Returns
    -------
    None
    """
    if scale_factor and target_height:
        print("Only one of scale_factor or target_height can be provided.")
        sys.exit(1)

    shape_context = StrategyContext()
    register_shape_strategies(shape_context)
    initialize_loaders()
    mesh_loader = LoaderFactory.get_loader("trimesh")
    model_factory = ModelFactory(mesh_loader)
    model = model_factory.create_model(stl_file, layer_height, scale_factor, target_height)

    config = ReferenceMarkConfig(
        tolerance=mark_tolerance,
        min_distance=mark_min_distance,
        available_shapes=[s.strip() for s in available_shapes.split(',') if s.strip()],
    )

    process_model(model, output_folder, shape_context, config)


if __name__ == '__main__':
    cli()
