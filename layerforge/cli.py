import sys
import math

import click

from layerforge.models import ModelFactory, SlicerService
from layerforge.models.reference_marks import ReferenceMarkConfig
from layerforge.models.loading import LoaderFactory
from layerforge.svg import SVGGenerator
from layerforge.svg.drawing import StrategyContext
from layerforge.utils import register_shape_strategies
from layerforge.utils.loader_initialization import initialize_loaders
from layerforge.writers import SVGFileWriter


def process_model(
    *,
    stl_file: str,
    layer_height: float,
    output_folder: str,
    scale_factor: float | None = None,
    target_height: float | None = None,
    mark_tolerance: float = 10.0,
    mark_min_distance: float = 10.0,
    available_shapes: str = "circle,square,triangle,arrow",
    mark_angle: float = 0.0,
    mark_color: str | None = None,
) -> None:
    """Process the model and generate SVG slices.

    Parameters
    ----------
    stl_file : str
        Path to the STL model to slice.
    layer_height : float
        Height of each generated layer.
    output_folder : str
        Directory where SVG slices will be written.
    scale_factor : float, optional
        Uniform scale factor to apply to the model.
    target_height : float, optional
        Desired overall height of the model.  Mutually exclusive with
        ``scale_factor``.
    mark_tolerance : float
        Distance used when matching existing marks.
    mark_min_distance : float
        Minimum distance from contours and between marks.
    available_shapes : str
        Comma separated list of shapes used for new marks.
    mark_angle : float
        Default orientation angle for marks in degrees.
    mark_color : str, optional
        Default color for mark outlines.

    Returns
    -------
    None
    """
    if scale_factor and target_height:
        click.echo("Only one of scale_factor or target_height can be provided.")
        sys.exit(1)

    shape_context = StrategyContext()
    register_shape_strategies(shape_context)
    initialize_loaders()
    mesh_loader = LoaderFactory.get_loader("trimesh")
    model_factory = ModelFactory(mesh_loader)
    model = model_factory.create_model(
        stl_file, layer_height, scale_factor, target_height
    )

    config = ReferenceMarkConfig(
        tolerance=mark_tolerance,
        min_distance=mark_min_distance,
        available_shapes=[s.strip() for s in available_shapes.split(",") if s.strip()],
        angle=math.radians(mark_angle),
        color=mark_color,
    )

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
@click.option(
    '--mark-tolerance',
    default=10.0,
    type=float,
    help='Tolerance when matching existing marks. '
    'See docs/reference_mark_algorithm.md#parameter-effects.'
)
@click.option(
    '--mark-min-distance',
    default=10.0,
    type=float,
    help='Minimum distance from contours and between marks. '
    'See docs/reference_mark_algorithm.md#parameter-effects.'
)
@click.option(
    '--available-shapes',
    default='circle,square,triangle,arrow',
    help='Comma separated list of mark shapes. '
    'See docs/reference_mark_algorithm.md#parameter-effects.'
)
@click.option(
    '--mark-angle',
    default=0.0,
    type=float,
    help='Default mark orientation in degrees. '
    'See docs/reference_mark_algorithm.md#parameter-effects.'
)
@click.option(
    '--mark-color',
    default=None,
    help='Outline color for marks. '
    'See docs/reference_mark_algorithm.md#parameter-effects.'
)
def cli(
    stl_file: str,
    layer_height: float,
    output_folder: str,
    scale_factor: float,
    target_height: float,
    mark_tolerance: float,
    mark_min_distance: float,
    available_shapes: str,
    mark_angle: float,
    mark_color: str,
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

    process_model(
        stl_file=stl_file,
        layer_height=layer_height,
        output_folder=output_folder,
        scale_factor=scale_factor,
        target_height=target_height,
        mark_tolerance=mark_tolerance,
        mark_min_distance=mark_min_distance,
        available_shapes=available_shapes,
        mark_angle=mark_angle,
        mark_color=mark_color,
    )


if __name__ == '__main__':
    cli()
