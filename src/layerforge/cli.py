import math
import tempfile
from pathlib import Path

import click

from layerforge.models import ModelFactory, SlicerService
from layerforge.models.loading import LoaderFactory
from layerforge.models.reference_marks import ReferenceMarkConfig
from layerforge.models.reference_marks.config import TOLERANCE_FACTOR
from layerforge.settings import Settings, find_config_file, merge_settings, read_config_file
from layerforge.svg import SVGGenerator
from layerforge.svg.drawing import StrategyContext
from layerforge.svg.style import SVGStyle
from layerforge.utils import register_shape_strategies
from layerforge.utils.loader_initialization import initialize_loaders
from layerforge.writers import SVGFileWriter

# The help text states each default from here, so it cannot drift from the settings.
_DEFAULTS = Settings()


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


def _lexists(path: Path) -> bool:
    """Return whether ``path`` exists, a dangling symlink included. Other errors are raised."""
    try:
        path.lstat()
    except (FileNotFoundError, NotADirectoryError):
        return False
    return True


def _check_output_folder(folder: str) -> None:
    """Reject an output folder that is empty, that is not a folder, or that cannot be written.

    ``lstat`` sees a dangling symlink, which ``exists`` does not and ``mkdir`` still fails on.
    Unlike ``lexists`` it does not hide an error such as a name that is too long.
    The folder is not made here, so a run that fails later leaves nothing behind. Instead a
    named temporary file is made and removed in the nearest folder that exists: that is the real
    operation, which an ``os.access`` guess misses for ACLs, and it is the folder the writer
    would have to make the new one in.
    """
    if not folder.strip():
        raise click.BadParameter("must not be empty", param_hint="--output-folder")
    path = Path(folder)
    try:
        blocker = next((p for p in (path, *path.parents) if _lexists(p)), None)
    except (OSError, ValueError) as exc:  # ValueError: an embedded null byte
        raise click.BadParameter(
            f"cannot use {folder}: {getattr(exc, 'strerror', None) or exc}",
            param_hint="--output-folder",
        ) from exc
    if blocker is None:
        return
    if not blocker.is_dir():
        raise click.BadParameter(f"{blocker} is not a folder", param_hint="--output-folder")
    try:
        with tempfile.NamedTemporaryFile(dir=blocker):
            pass
    except OSError as exc:
        raise click.BadParameter(
            f"cannot write to {blocker}: {exc.strerror or exc}", param_hint="--output-folder"
        ) from exc


def _read_settings_file(config_path: Path | None) -> tuple[Settings, Path | None]:
    """Read and check the config file once. Return its settings, and the file that was used."""
    path = find_config_file(config_path)
    return (read_config_file(path) if path is not None else Settings()), path


def resolve_settings(
    file_settings: Settings,
    *,
    output_folder: str,
    units: str | None = None,
    layer_height: float | None = None,
    kerf: float | None = None,
    scale_factor: float | None = None,
    target_height: float | None = None,
    mark_size: float | None = None,
    mark_tolerance: float | None = None,
    mark_min_distance: float | None = None,
    available_shapes: str | None = None,
    mark_angle: float | None = None,
    cut_color: str | None = None,
    engrave_color: str | None = None,
) -> Settings:
    """Check every option against the settings of the config file, and return the run's settings.

    The command calls this before it asks for the STL path, so nothing is asked
    for when a check fails. The file was checked first (``_read_settings_file``, exit 2).
    The order here is the scale and target conflict (exit 1), then the bad values (exit 2),
    with the output folder last.
    """
    if scale_factor is not None and target_height is not None:
        raise ConflictingOptionsError("Only one of scale_factor or target_height can be provided.")
    _check_positive(scale_factor, "--scale-factor")
    _check_positive(target_height, "--target-height")

    shapes = None
    if available_shapes is not None:
        shapes = [s.strip() for s in available_shapes.split(",") if s.strip()]
    settings = merge_settings(
        file_settings,
        {
            "units": units,
            "layer_height": layer_height,
            "kerf": kerf,
            "mark_size": mark_size,
            "mark_tolerance": mark_tolerance,
            "mark_min_distance": mark_min_distance,
            "available_shapes": shapes,
            "mark_angle": mark_angle,
            "cut_color": cut_color,
            "engrave_color": engrave_color,
        },
    )
    _check_output_folder(output_folder)
    return settings


def _run(
    settings: Settings,
    *,
    stl_file: str,
    output_folder: str,
    scale_factor: float | None,
    target_height: float | None,
) -> None:
    """Load the model, slice it and write the SVG files. The settings are already checked."""
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
        min_web_ratio=marks.min_web_ratio,
        kerf=settings.kerf,
        min_hole_ratio=marks.min_hole_ratio,
        min_hole_kerf_factor=marks.min_hole_kerf_factor,
    )

    slices = SlicerService.slice_model(model, config=config)
    svg_writer = SVGFileWriter()
    output = settings.output
    style = SVGStyle(
        cut_color=output.cut_color,
        engrave_color=output.engrave_color,
        hairline_width=output.hairline_width,
    )
    svg_generator = SVGGenerator(
        output_folder, svg_writer, shape_context, units=settings.units, style=style
    )
    svg_generator.generate_svgs(slices)


def process_model(
    *,
    stl_file: str,
    output_folder: str,
    units: str | None = None,
    layer_height: float | None = None,
    kerf: float | None = None,
    scale_factor: float | None = None,
    target_height: float | None = None,
    mark_size: float | None = None,
    mark_tolerance: float | None = None,
    mark_min_distance: float | None = None,
    available_shapes: str | None = None,
    mark_angle: float | None = None,
    cut_color: str | None = None,
    engrave_color: str | None = None,
    config_path: Path | None = None,
) -> None:
    """Process the model and generate SVG slices.

    Parameters
    ----------
    stl_file : str
        Path to the STL model to slice.
    output_folder : str
        Directory where SVG slices will be written.
    units : str, optional
        The unit of the model and of every length: ``mm``, ``cm`` or ``in``. It sets
        the unit of each SVG's size. Falls back to the config file, then its default.
    layer_height : float, optional
        Height of each generated layer, which is the thickness of the sheet. Falls back to the
        config file, then its default (3 mm, stated in ``units``).
    kerf : float, optional
        The width of material the tool removes. Falls back to the config file, then its
        default (0.3 mm, stated in ``units``).
    scale_factor : float, optional
        Uniform scale factor to apply to the model.
    target_height : float, optional
        Desired overall height of the model.  Mutually exclusive with
        ``scale_factor``.
    mark_size : float, optional
        Size of every new mark. Without it the size follows the layer height and the kerf (TR-6).
    mark_tolerance : float, optional
        Distance used when matching existing marks. Without it, 0.1 times the mark size.
    mark_min_distance : float, optional
        Minimum distance from contours and between marks. Without it, the mark size.
    available_shapes : str, optional
        Comma separated list of shapes used for new marks.
    mark_angle : float, optional
        Default orientation angle for marks in degrees.
    cut_color : str, optional
        The stroke colour of everything that is cut: the outlines and the mark holes. A name,
        #rgb, #rrggbb or rgb(r,g,b). Falls back to the config file, then its default (red).
    engrave_color : str, optional
        The colour of the number, which is engraved. Falls back to the config file, then its
        default (black).
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
    # The same steps as ``cli``, without the message and the prompt. They are kept apart on
    # purpose: ``test_cli_checks_before_prompt`` runs every check through both, so they
    # cannot drift.
    file_settings, _ = _read_settings_file(config_path)
    settings = resolve_settings(
        file_settings,
        output_folder=output_folder,
        units=units,
        layer_height=layer_height,
        kerf=kerf,
        scale_factor=scale_factor,
        target_height=target_height,
        mark_size=mark_size,
        mark_tolerance=mark_tolerance,
        mark_min_distance=mark_min_distance,
        available_shapes=available_shapes,
        mark_angle=mark_angle,
        cut_color=cut_color,
        engrave_color=engrave_color,
    )
    _run(
        settings,
        stl_file=stl_file,
        output_folder=output_folder,
        scale_factor=scale_factor,
        target_height=target_height,
    )


@click.command()
@click.option(
    "--stl-file",
    default=None,
    help="The path to the STL file. Asked for, after the options are checked, if not given.",
)
@click.option(
    "--config",
    "config_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="A TOML settings file. Default: layerforge.toml in the current directory, if it exists. "
    "The command line overrides the file. The file that is used is named on stderr.",
)
@click.option(
    "--units",
    default=None,
    type=click.Choice(["mm", "cm", "in"]),
    help="The unit of the model and of every length option. It sets the physical size "
    "of each SVG. An STL file has no unit, so this states it and nothing is converted. "
    f"Default {_DEFAULTS.units}.",
)
@click.option(
    "--layer-height",
    default=None,
    type=float,
    help="The layer height, which is the thickness of the sheet. "
    f"Default {_DEFAULTS.layer_height} mm, stated in --units.",
)
@click.option(
    "--kerf",
    default=None,
    type=float,
    help="The kerf: the width of material the tool removes. It sets the smallest default "
    f"mark size ({_DEFAULTS.marks.min_hole_kerf_factor:g} x the kerf). "
    f"Default {_DEFAULTS.kerf} mm, stated in --units. Use 0 for a CNC router or hand work.",
)
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
    help="Size of every new mark. Default: the larger of "
    f"{_DEFAULTS.marks.min_hole_ratio:g} x the layer height and "
    f"{_DEFAULTS.marks.min_hole_kerf_factor:g} x the kerf.",
)
@click.option(
    "--mark-tolerance",
    default=None,
    type=float,
    help="Tolerance when matching existing marks. "
    f"Default {TOLERANCE_FACTOR:g} x the mark size. "
    "See docs/reference_mark_algorithm.md#parameter-effects.",
)
@click.option(
    "--mark-min-distance",
    default=None,
    type=float,
    help="Minimum distance from contours and between marks. "
    "Default: the mark size. "
    "See docs/reference_mark_algorithm.md#parameter-effects.",
)
@click.option(
    "--available-shapes",
    default=None,
    help="Comma separated list of mark shapes. "
    f"Default {','.join(_DEFAULTS.marks.shapes)}. "
    "See docs/reference_mark_algorithm.md#parameter-effects.",
)
@click.option(
    "--mark-angle",
    default=None,
    type=float,
    help=f"Default mark orientation in degrees. Default {_DEFAULTS.marks.angle}. "
    "See docs/reference_mark_algorithm.md#parameter-effects.",
)
@click.option(
    "--cut-color",
    default=None,
    help="The stroke colour of everything that is cut: the outlines and the mark holes. "
    "An SVG colour such as red, #f00 or rgb(255,0,0). Laser software groups objects by "
    f"colour, and you set the operation for each group. Default {_DEFAULTS.output.cut_color}.",
)
@click.option(
    "--engrave-color",
    default=None,
    help="The colour of the number, which is engraved. A name, #rgb, #rrggbb or rgb(r,g,b). "
    f"Default {_DEFAULTS.output.engrave_color}.",
)
def cli(
    stl_file: str | None,
    config_path: Path | None,
    units: str | None,
    layer_height: float | None,
    kerf: float | None,
    output_folder: str,
    scale_factor: float | None,
    target_height: float | None,
    mark_size: float | None,
    mark_tolerance: float | None,
    mark_min_distance: float | None,
    available_shapes: str | None,
    mark_angle: float | None,
    cut_color: str | None,
    engrave_color: str | None,
) -> None:
    """Slice an STL model into one SVG file per layer.

    A setting comes from the command line first, then from a TOML file (--config,
    or layerforge.toml in the current directory), then from its default. Every
    option and the file are checked before the STL path is asked for.
    """
    try:
        file_settings, used_file = _read_settings_file(config_path)
        if used_file is not None:
            click.echo(f"Using settings from {used_file}", err=True)
        settings = resolve_settings(
            file_settings,
            output_folder=output_folder,
            units=units,
            layer_height=layer_height,
            kerf=kerf,
            scale_factor=scale_factor,
            target_height=target_height,
            mark_size=mark_size,
            mark_tolerance=mark_tolerance,
            mark_min_distance=mark_min_distance,
            available_shapes=available_shapes,
            mark_angle=mark_angle,
            cut_color=cut_color,
            engrave_color=engrave_color,
        )
    except ConflictingOptionsError as exc:
        click.echo(str(exc))
        raise SystemExit(1) from exc
    if stl_file is None:
        stl_file = click.prompt("STL file path", type=str)
    _run(
        settings,
        stl_file=stl_file,
        output_folder=output_folder,
        scale_factor=scale_factor,
        target_height=target_height,
    )


if __name__ == "__main__":
    cli()
