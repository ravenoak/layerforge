"""A mark is a hole with an extent (TR-5). Clearance is checked on the whole hole."""

import logging
import math

import pytest
from click.testing import CliRunner
from shapely.geometry import Polygon, box

pytest.importorskip("trimesh")
import trimesh

from layerforge.cli import cli
from layerforge.models.reference_marks import (
    ReferenceMark,
    ReferenceMarkAdjuster,
    ReferenceMarkCalculator,
    ReferenceMarkConfig,
    ReferenceMarkManager,
    ReferenceMarkService,
    mark_reach,
)
from layerforge.models.slicing.slice import Slice

PIECE = box(0, 0, 20, 20)


def _adjust(marks, contours=None, **config):
    cfg = ReferenceMarkConfig(**config)
    return ReferenceMarkAdjuster.adjust_marks(marks, contours or [PIECE], config=cfg)


def test_an_arrow_whose_tip_touches_the_outline_is_dropped():
    # The centre is 4 from the edge, so the centre rule alone keeps it.
    arrow = ReferenceMark(16, 10, "arrow", 8, angle=0.0)
    assert _adjust([arrow], min_distance=2) == []


def test_the_same_arrow_turned_away_from_the_outline_is_kept():
    arrow = ReferenceMark(16, 10, "arrow", 8, angle=math.pi)
    assert _adjust([arrow], min_distance=2) == [arrow]


def test_a_circle_that_crosses_the_outline_is_dropped():
    circle = ReferenceMark(3, 10, "circle", 8)
    assert _adjust([circle], min_distance=1) == []


def test_two_holes_that_overlap_are_not_both_kept():
    # Centres 3 apart pass min_distance 1, but two holes of size 4 overlap.
    first, second = ReferenceMark(8, 10, "circle", 4), ReferenceMark(11, 10, "circle", 4)
    assert _adjust([first, second], min_distance=1) == [first]


def test_a_mark_outside_every_contour_is_dropped_even_with_min_distance_zero():
    """#108 item 2."""
    assert _adjust([ReferenceMark(30, 10, "circle", 2)], min_distance=0) == []


def test_a_mark_inside_a_hole_of_the_piece_is_dropped_even_with_min_distance_zero():
    plate = Polygon([(0, 0), (40, 0), (40, 40), (0, 40)], [box(10, 10, 30, 30).exterior.coords])
    assert _adjust([ReferenceMark(20, 20, "circle", 2)], [plate], min_distance=0) == []


def test_a_hole_too_close_to_the_outline_for_the_web_is_dropped():
    # Size 4 at x = 3: the hole reaches x = 1, so 1 unit of material is left.
    circle = ReferenceMark(3, 10, "circle", 4)
    cfg = ReferenceMarkConfig(min_distance=1)
    assert ReferenceMarkAdjuster.adjust_marks([circle], [PIECE], cfg, min_web=1.5) == []
    assert ReferenceMarkAdjuster.adjust_marks([circle], [PIECE], cfg, min_web=0.5) == [circle]


def test_two_holes_closer_than_the_web_are_not_both_kept():
    # Size 4, centres 4.5 apart: 0.5 of material is left between the holes.
    first, second = ReferenceMark(8, 10, "circle", 4), ReferenceMark(12.5, 10, "circle", 4)
    cfg = ReferenceMarkConfig(min_distance=1)
    kept = ReferenceMarkAdjuster.adjust_marks([first, second], [PIECE], cfg, min_web=1.5)
    assert kept == [first]
    kept = ReferenceMarkAdjuster.adjust_marks([first, second], [PIECE], cfg, min_web=0.4)
    assert kept == [first, second]


def test_the_web_ratio_defaults_to_half_the_layer_height():
    assert ReferenceMarkConfig().min_web_ratio == 0.5


BAR = box(0, 0, 40, 6)


def _slice(polygon, layer_height=3.0, **config):
    cfg = ReferenceMarkConfig(**config)
    return Slice(
        0,
        0.0,
        [polygon],
        origin=(0, 0),
        mark_manager=ReferenceMarkManager(config=cfg),
        config=cfg,
        layer_height=layer_height,
    )


def test_the_calculator_does_not_choose_a_point_whose_hole_would_cross_the_outline():
    # The centre of the bar is 3 from each edge, so the centre rule passes for size 8.
    layer = _slice(BAR, size=8, min_distance=1)
    assert ReferenceMarkCalculator.get_stable_marks(layer, [], config=layer.config) == []


def test_the_calculator_does_not_inherit_a_mark_whose_hole_would_cross_the_outline():
    layer = _slice(BAR, size=8, min_distance=1)
    assert ReferenceMarkCalculator.get_stable_marks(layer, [(20, 3)], config=layer.config) == []


def test_the_web_comes_from_the_layer_height_and_the_ratio():
    # Size 3 has a radius of 1.5. The bar leaves 3 - 1.5 = 1.5 from hole to edge.
    thick = _slice(BAR, layer_height=4.0, size=3, min_distance=1)  # web 0.5 * 4 = 2
    thin = _slice(BAR, layer_height=2.0, size=3, min_distance=1)  # web 0.5 * 2 = 1
    no_web = _slice(BAR, layer_height=4.0, size=3, min_distance=1, min_web_ratio=0)  # web 0
    for layer in (thick, thin, no_web):
        ReferenceMarkService.process_slice(layer)
    assert (len(thick.ref_marks), len(thin.ref_marks), len(no_web.ref_marks)) == (0, 1, 1)


def test_the_warning_for_a_slice_without_marks_names_the_mark_size_too(caplog):
    layer = _slice(BAR, size=8, min_distance=1)
    with caplog.at_level(logging.WARNING):
        ReferenceMarkService.process_slice(layer)
    (record,) = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert "--mark-min-distance" in record.getMessage()
    assert "--mark-size" in record.getMessage()


def _run_bar(tmp_path, width, *args, config=None):
    """Slice a 20 x ``width`` x 10 bar in two layers of 5 and return slice 0 as text."""
    stl = tmp_path / "bar.stl"
    trimesh.creation.box(extents=(20, width, 10)).export(stl)
    out = tmp_path / "out"
    options = ["--stl-file", str(stl), "--layer-height", "5", "--output-folder", str(out)]
    if config is not None:
        (tmp_path / "web.toml").write_text(config)
        options += ["--config", str(tmp_path / "web.toml")]
    result = CliRunner().invoke(
        cli, [*options, "--mark-size", "2", "--mark-min-distance", "1", *args]
    )
    assert result.exit_code == 0, result.output
    return (out / "slice_000.svg").read_text()


def test_the_command_keeps_a_hole_with_enough_material_around_it(tmp_path):
    # A bar 8 wide: the hole (size 2) is 3 from each edge, and the web is 0.5 x 5 = 2.5.
    assert "<circle" in _run_bar(tmp_path, 8)


def test_the_command_drops_a_hole_with_too_little_material_around_it(tmp_path):
    # A bar 6 wide: the hole is 2 from each edge, less than the web of 2.5.
    assert "<circle" not in _run_bar(tmp_path, 6)


def test_the_web_ratio_of_the_config_file_reaches_the_slices(tmp_path):
    assert "<circle" in _run_bar(tmp_path, 6, config="[marks]\nmin_web_ratio = 0.2\n")
    assert "<circle" not in _run_bar(tmp_path, 8, config="[marks]\nmin_web_ratio = 0.7\n")


@pytest.mark.parametrize("side", [6.0, 6.002, 6.005])
@pytest.mark.parametrize("shape", ["circle", "square", "triangle", "arrow"])
def test_every_point_the_calculator_chooses_survives_the_adjuster(shape, side):
    """#157: the calculator's disc must hold the hole that the adjuster checks.

    Size 3 and layer height 3 give a web of 1.5, so the centre of a 6 wide piece is
    exactly at the calculator's limit. The circle's outline reaches 1.5018, past its disc.
    """
    piece = box(0, 0, side, side)
    config = {"size": 3, "min_distance": 3, "available_shapes": [shape]}
    chosen = ReferenceMarkCalculator.get_stable_marks(
        _slice(piece, layer_height=3.0, **config),
        [],
        config=ReferenceMarkConfig(**config),
    )
    layer = _slice(piece, layer_height=3.0, **config)
    ReferenceMarkService.process_slice(layer)
    assert len(layer.ref_marks) == len(chosen)


def test_the_check_of_a_circle_agrees_with_the_drawn_circle_at_the_boundary():
    """#157: the outline lies outside the drawn circle, so a circle that crosses is never kept.

    The drawn circle of size 3 has radius 1.5. A piece 0.0005 narrower than the circle on
    each side is crossed by it, and a piece 0.005 wider than the outline's reach is not.
    """
    circle = ReferenceMark(0, 0, "circle", 3)
    crossed = box(-1.4995, -1.4995, 1.4995, 1.4995)
    clear = box(-1.508, -1.508, 1.508, 1.508)
    assert _adjust([circle], [crossed], min_distance=0) == []
    assert _adjust([circle], [clear], min_distance=0) == [circle]


def test_the_reach_of_the_circle_is_a_little_over_half_its_size_and_the_others_are_half():
    """#157: measured on the outline that the adjuster checks."""
    assert mark_reach("circle", 10) == pytest.approx(5 / math.cos(math.pi / 64))
    for name in ("square", "triangle", "arrow"):
        assert mark_reach(name, 10) == pytest.approx(5.0)


def test_the_calculator_refuses_a_shape_name_that_is_not_registered():
    """The disc is sized by the outlines of the available shapes, so an unknown name raises."""
    layer = _slice(box(0, 0, 40, 40), layer_height=3.0, available_shapes=["hexagon"])
    with pytest.raises(ValueError, match="hexagon"):
        ReferenceMarkCalculator.get_stable_marks(layer, [], config=layer.config)


def test_a_mark_with_an_unregistered_shape_name_is_an_error_and_not_a_skipped_check():
    """#162: the error reaches the caller, so the circle at (1, 1) is not kept unchecked.

    Before, `Slice.adjust_marks` caught the error, logged one line and kept both marks,
    including the circle whose hole crosses the outline.
    """
    layer = _slice(box(0, 0, 40, 40), layer_height=3.0, min_distance=1)
    marks = [ReferenceMark(20, 20, "hexagon", 4), ReferenceMark(1, 1, "circle", 4)]
    layer.ref_marks = list(marks)
    with pytest.raises(ValueError, match="hexagon"):
        layer.adjust_marks()
    assert layer.ref_marks == marks


def test_an_unregistered_shape_name_is_an_error_even_for_a_mark_that_is_too_close_to_an_edge():
    """#162: the name is checked for every mark, not only for those that pass the centre rule."""
    layer = _slice(box(0, 0, 40, 40), layer_height=3.0, min_distance=2)
    layer.ref_marks = [ReferenceMark(1, 1, "hexagon", 4)]
    with pytest.raises(ValueError, match="hexagon"):
        layer.adjust_marks()
