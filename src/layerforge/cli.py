import math
from pathlib import Path

import click

from layerforge.models import ModelFactory, SlicerService
from layerforge.models.loading import LoaderFactory
from layerforge.models.reference_marks import ReferenceMarkConfig
from layerforge.settings import load_settings
from layerforge.svg import SVGGenerator
from layerforge.svg.drawing import StrategyContext
from layerforge.utils import register_shape_strategies
from layerforge.utils.loader_initialization import initialize_loaders
from layerforge.writers import SVGFileWriter


class ConflictingOptionsError(ValueError):
    """Raised when mutually exclusive CLI options are provided."""


def _check_positive(value: float | None, hint: str) -> None:
    """Reject a number that is not finite or not above 0. ``None`` passes."""
    if value is None:
        return
    if not math.isfinite(value):
        raise click.BadParameter("must be a finite number", param_hint=hint)
    if value <= 0:
        raise click.BadParameter("must be > 0", param_hint=hint)


def process_model(
    *,
    stl_file: str,
    output_folder: str,
    layer_height: float | None = None,
    scale_factor: float | None = None,
    target_height: float | None = None,
    mark_size: float | None = None,
    mark_tolerance: float | None = None,
    mark_min_distance: float | None = None,
    available_shapes: str | None = None,
    mark_angle: float | None = None,
    mark_color: str | None = None,
    config_path: Path | None = None,
) -> None:
    """Process the model and generate SVG slices.

    Parameters
    ----------
    stl_file : str
        Path to the STL model to slice.
    output_folder : str
        Directory where SVG slices will be written.
    layer_height : float, optional
        Height of each generated layer. Falls back to the config file, then 3.0.
    scale_factor : float, optional
        Uniform scale factor to apply to the model.
    target_height : float, optional
        Desired overall height of the model.  Mutually exclusive with
        ``scale_factor``.
    mark_size : float, optional
        Size of every new mark. Without it the size follows the distance from
        the origin.
    mark_tolerance : float, optional
        Distance used when matching existing marks.
    mark_min_distance : float, optional
        Minimum distance from contours and between marks.
    available_shapes : str, optional
        Comma separated list of shapes used for new marks.
    mark_angle : float, optional
        Default orientation angle for marks in degrees.
    mark_color : str, optional
        Default color for mark outlines.
    config_path : Path, optional
        The TOML config file. Without it ``layerforge.toml`` in the current
        directory is used if it exists.

    Notes
    -----
    A setting that is ``None`` here comes from the config file, then its default.

    Returns
    -------
    None
    """
    if scale_factor is not None and target_height is not None:
        raise ConflictingOptionsError("Only one of scale_factor or target_height can be provided.")

    _check_positive(scale_factor, "--scale-factor")
    _check_positive(target_height, "--target-height")

    shapes = None
    if available_shapes is not None:
        shapes = [s.strip() for s in available_shapes.split(",") if s.strip()]
    settings = load_settings(
        config_path,
        {
            "layer_height": layer_height,
            "mark_size": mark_size,
            "mark_tolerance": mark_tolerance,
            "mark_min_distance": mark_min_distance,
            "available_shapes": shapes,
            "mark_angle": mark_angle,
        },
    )

    shape_context = StrategyContext()
    register_shape_strategies(shape_context)
    initialize_loaders()
    mesh_loader = LoaderFactory.get_loader("trimesh")
    model_factory = ModelFactory(mesh_loader)
    try:
        model = model_factory.create_model(
            stl_file, settings.layer_height, scale_factor, target_height
        )
    except ValueError as exc:
        raise click.ClickException(f"Cannot load '{stl_file}': {exc}") from exc

    marks = settings.marks
    config = ReferenceMarkConfig(
        tolerance=marks.tolerance,
        min_distance=marks.min_distance,
        available_shapes=marks.shapes,
        angle=math.radians(marks.angle),
        size=marks.size,
        color=mark_color,
    )

    slices = SlicerService.slice_model(model, config=config)
    svg_writer = SVGFileWriter()
    svg_generator = SVGGenerator(output_folder, svg_writer, shape_context)
    svg_generator.generate_svgs(slices)


@click.command()
@click.option("--stl-file", prompt="STL file path", help="The path to the STL file.")
@click.option(
    "--config",
    "config_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="A TOML settings file. Default: layerforge.toml in the current directory, if it exists. "
    "The command line overrides the file.",
)
@click.option("--layer-height", default=None, type=float, help="The layer height. Default 3.0.")
@click.option("--output-folder", default="output", help="The output folder for SVG files.")
@click.option(
    "--scale-factor",
    default=None,
    type=float,
    help="The scale factor to apply to the model.",
)
@click.option("--target-height", default=None, type=float, help="The target height for the model.")
@click.option(
    "--mark-size",
    default=None,
    type=float,
    help="Size of every new mark. Default: 3 to 5, by distance from the model origin.",
)
@click.option(
    "--mark-tolerance",
    default=None,
    type=float,
    help="Tolerance when matching existing marks. Default 10.0. "
    "See docs/reference_mark_algorithm.md#parameter-effects.",
)
@click.option(
    "--mark-min-distance",
    default=None,
    type=float,
    help="Minimum distance from contours and between marks. Default 10.0. "
    "See docs/reference_mark_algorithm.md#parameter-effects.",
)
@click.option(
    "--available-shapes",
    default=None,
    help="Comma separated list of mark shapes. Default circle,square,triangle,arrow. "
    "See docs/reference_mark_algorithm.md#parameter-effects.",
)
@click.option(
    "--mark-angle",
    default=None,
    type=float,
    help="Default mark orientation in degrees. Default 0.0. "
    "See docs/reference_mark_algorithm.md#parameter-effects.",
)
@click.option(
    "--mark-color",
    default=None,
    help="Outline color for marks. See docs/reference_mark_algorithm.md#parameter-effects.",
)
def cli(
    stl_file: str,
    config_path: Path | None,
    layer_height: float | None,
    output_folder: str,
    scale_factor: float | None,
    target_height: float | None,
    mark_size: float | None,
    mark_tolerance: float | None,
    mark_min_distance: float | None,
    available_shapes: str | None,
    mark_angle: float | None,
    mark_color: str | None,
) -> None:
    """Entry point for the CLI.

    This function wraps all the logic for processing an STL file and
    generating SVG slices while accepting commandline arguments.
    See ``README.md`` for example usage.

    Parameters
    ----------
    stl_file : str
        The path to the STL file.
    config_path : Path, optional
        The TOML settings file.
    layer_height : float, optional
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

    try:
        process_model(
            stl_file=stl_file,
            config_path=config_path,
            layer_height=layer_height,
            output_folder=output_folder,
            scale_factor=scale_factor,
            target_height=target_height,
            mark_size=mark_size,
            mark_tolerance=mark_tolerance,
            mark_min_distance=mark_min_distance,
            available_shapes=available_shapes,
            mark_angle=mark_angle,
            mark_color=mark_color,
        )
    except ConflictingOptionsError as exc:
        click.echo(str(exc))
        raise SystemExit(1) from exc


if __name__ == "__main__":
    cli()
