"""Which pieces of adjacent layers overlap, and where (TR-2, TR-9, #89)."""

import math

import pytest
from shapely import make_valid
from shapely.geometry import MultiPolygon, Point, Polygon, box

from layerforge.models.slicing.adjacency import AdjacentPair, adjacent_pairs


def _pairs(layers, **kwargs):
    return adjacent_pairs(layers, **kwargs)


def test_a_box_on_a_box_gives_one_pair():
    result = _pairs([[box(0, 0, 10, 10)], [box(2, 2, 12, 12)]])

    assert len(result) == 1
    (pair,) = result[0]
    assert (pair.lower, pair.upper) == (0, 0)
    assert pair.overlap.equals(box(2, 2, 10, 10))
    assert pair.shrunk.equals(pair.overlap)  # no clearance


def test_a_tube_on_a_solid_cylinder_gives_one_pair_whose_overlap_has_a_hole():
    tube = Point(0, 0).buffer(10).difference(Point(0, 0).buffer(5))
    solid = Point(0, 0).buffer(10)

    (pair,) = _pairs([[solid], [tube]])[0]

    assert isinstance(pair.overlap, Polygon)
    assert len(pair.overlap.interiors) == 1
    assert pair.overlap.area == pytest.approx(tube.area)


def test_two_pieces_on_one_piece_give_two_pairs():
    result = _pairs([[box(0, 0, 30, 10)], [box(0, 0, 10, 10), box(20, 0, 30, 10)]])

    assert [(p.lower, p.upper) for p in result[0]] == [(0, 0), (0, 1)]


def test_one_piece_on_two_pieces_gives_two_pairs():
    result = _pairs([[box(0, 0, 10, 10), box(20, 0, 30, 10)], [box(0, 0, 30, 10)]])

    assert [(p.lower, p.upper) for p in result[0]] == [(0, 0), (1, 0)]


def test_pieces_that_do_not_overlap_give_no_pair():
    assert _pairs([[box(0, 0, 10, 10)], [box(20, 0, 30, 10)]]) == [[]]


@pytest.mark.parametrize(
    "upper", [box(10, 0, 20, 10), box(10, 10, 20, 20)], ids=["shared edge", "shared corner"]
)
def test_pieces_that_only_touch_give_no_pair(upper):
    assert _pairs([[box(0, 0, 10, 10)], [upper]]) == [[]]


def test_a_sliver_below_the_threshold_gives_no_pair():
    layers = [[box(0, 0, 10, 10)], [box(9, 0, 20, 10)]]  # overlap area 10.0

    assert _pairs(layers, min_overlap_area=10.5) == [[]]
    assert len(_pairs(layers, min_overlap_area=10.0)[0]) == 1  # at the threshold counts


def test_a_piece_inside_another_overlaps_it():
    """``Polygon.overlaps`` is False for containment, and containment counts here."""
    (pair,) = _pairs([[box(0, 0, 10, 10)], [box(4, 4, 6, 6)]])[0]

    assert pair.overlap.equals(box(4, 4, 6, 6))


def test_a_u_on_a_bar_gives_an_overlap_in_two_parts():
    u = Polygon([(0, 0), (10, 0), (10, 10), (7, 10), (7, 3), (3, 3), (3, 10), (0, 10)])
    bar = box(0, 0, 10, 2)  # covers the base of the U only: one part
    arms = box(0, 5, 10, 8)  # crosses both arms: two parts

    (pair,) = _pairs([[u], [arms]])[0]

    assert isinstance(pair.overlap, MultiPolygon)
    assert len(pair.overlap.geoms) == 2
    (base,) = _pairs([[u], [bar]])[0]
    assert isinstance(base.overlap, Polygon)


def test_the_shrunk_overlap_is_the_overlap_moved_in_by_the_clearance():
    (pair,) = _pairs([[box(0, 0, 10, 10)], [box(0, 0, 10, 10)]], clearance=2.0)[0]

    assert pair.shrunk.equals(box(2, 2, 8, 8))
    assert pair.overlap.equals(box(0, 0, 10, 10))


def test_the_shrunk_overlap_is_empty_when_the_clearance_is_larger_than_the_overlap():
    (pair,) = _pairs([[box(0, 0, 10, 10)], [box(0, 0, 10, 10)]], clearance=5.0)[0]

    assert pair.shrunk.is_empty
    assert not pair.overlap.is_empty


def test_pairs_are_listed_for_each_lower_layer():
    layers = [[box(0, 0, 10, 10)], [box(0, 0, 10, 10)], [box(50, 0, 60, 10)]]

    result = _pairs(layers)

    assert [len(pairs) for pairs in result] == [1, 0]


@pytest.mark.parametrize("layers", [[], [[box(0, 0, 1, 1)]]])
def test_fewer_than_two_layers_give_no_list(layers):
    assert _pairs(layers) == []


def test_an_empty_layer_gives_no_pair():
    assert _pairs([[], [box(0, 0, 1, 1)]]) == [[]]


@pytest.mark.parametrize("bad", [-1.0, math.nan, math.inf])
@pytest.mark.parametrize("name", ["min_overlap_area", "clearance"])
def test_a_bad_number_raises(name, bad):
    with pytest.raises(ValueError, match=name):
        _pairs([[box(0, 0, 1, 1)], [box(0, 0, 1, 1)]], **{name: bad})


def test_a_pair_is_immutable():
    (pair,) = _pairs([[box(0, 0, 1, 1)], [box(0, 0, 1, 1)]])[0]

    assert isinstance(pair, AdjacentPair)
    with pytest.raises(AttributeError):
        pair.lower = 3  # type: ignore[misc]


def test_an_edge_that_only_touches_is_not_part_of_the_overlap():
    """The C wraps round the top of the box: it overlaps the bottom and touches the top edge."""
    c = Polygon([(-5, 0), (10, 0), (10, 2), (-1, 2), (-1, 10), (10, 10), (10, 12), (-5, 12)])

    (pair,) = _pairs([[box(0, 0, 10, 10)], [c]])[0]

    assert isinstance(pair.overlap, Polygon)
    assert pair.overlap.equals(box(0, 0, 10, 2))


def test_a_repairable_invalid_polygon_does_not_raise():
    # A bow-tie: self-intersecting but shapely.make_valid can repair it.
    bowtie = Polygon([(0, 0), (10, 10), (10, 0), (0, 10)])
    normal = Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])
    result = adjacent_pairs([[bowtie], [normal]])
    assert len(result) == 1


def test_a_polygon_that_repairs_into_a_geometrycollection_does_not_raise():
    """Review fix: `make_valid` can return a `GeometryCollection` holding a `MultiPolygon`
    plus the leftover line of a self-intersection, not just a bare `Polygon`/`MultiPolygon`.
    `shapely.get_parts` does not descend into that `MultiPolygon`'s own pieces, so a naive
    `isinstance(part, Polygon)` filter over `get_parts(repaired)` sees no `Polygon` at all and
    wrongly raises, though the shape has 50 units of real, repairable area (see
    `layerforge.utils.polygon_parts`)."""
    spiky = Polygon([(0, 0), (10, 10), (10, 0), (0, 10), (0, 0), (5, 0), (5, -5), (5, 0)])
    assert make_valid(spiky).geom_type == "GeometryCollection"  # pins the repro, not the fix
    normal = Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])
    result = adjacent_pairs([[spiky], [normal]])
    assert len(result) == 1


def test_an_unrepairable_polygon_raises_a_value_error_naming_the_piece():
    # A zero-area closed line: invalid, and make_valid resolves it to a MultiLineString
    # with no polygon parts, so it cannot be repaired into a polygon with area.
    degenerate = Polygon([(0, 0), (5, 5), (10, 10), (0, 0)])
    normal = Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])
    with pytest.raises(ValueError, match="layer 0 piece 0"):
        adjacent_pairs([[degenerate], [normal]])
