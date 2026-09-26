"""Where the layer number goes (TR-11): clear of the outline, the holes and the marks."""

import pytest
from shapely.geometry import Polygon, box

from layerforge.models.reference_marks import ReferenceMark
from layerforge.models.slicing.number import largest_fitting_height, number_box, place_number

H = 2.0  # number height
W = 0.6  # width factor


def _place(contour, marks=(), *, digits=1, clearance=0.0):
    return place_number(
        contour, list(marks), digits=digits, height=H, width_factor=W, clearance=clearance
    )


def _inside_clear(contour, marks, placement, digits, clearance):
    """The number's box lies in the contour, ``clearance`` from its edges and from the holes."""
    b = number_box(placement.x, placement.y, digits=digits, height=H, width_factor=W)
    return contour.buffer(-clearance + 1e-9).contains(b)


def test_a_square_gets_the_number_at_its_centre():
    placement = _place(box(0, 0, 10, 10))
    assert placement.fits
    assert (placement.x, placement.y) == pytest.approx((5, 5), abs=0.1)


def test_an_l_shape_puts_the_number_clear_of_the_inner_corner():
    l_shape = Polygon([(0, 0), (10, 0), (10, 4), (4, 4), (4, 10), (0, 10)])
    placement = _place(l_shape)
    assert placement.fits
    assert _inside_clear(l_shape, [], placement, 1, 0.0)


def test_a_plate_with_a_hole_keeps_the_number_out_of_the_hole():
    plate = Polygon(
        [(0, 0), (100, 0), (100, 100), (0, 100)], holes=[[(30, 30), (70, 30), (70, 70), (30, 70)]]
    )
    placement = _place(plate)
    assert placement.fits
    b = number_box(placement.x, placement.y, digits=1, height=H, width_factor=W)
    assert plate.contains(b)


def test_a_mark_at_the_centre_moves_the_number_away_from_it():
    square = box(0, 0, 20, 10)
    mark = ReferenceMark(10, 5, "circle", 4.0, 0.0)
    placement = _place(square, [mark])
    assert placement.fits
    b = number_box(placement.x, placement.y, digits=1, height=H, width_factor=W)
    assert not b.intersects(box(8, 3, 12, 7))  # the circle of size 4 at (10, 5)


def test_the_clearance_is_kept_from_the_outline():
    square = box(0, 0, 10, 10)
    placement = _place(square, clearance=1.0)
    assert placement.fits
    assert _inside_clear(square, [], placement, 1, 1.0)


def test_two_digits_need_a_wider_box():
    strip = box(0, 0, 1.5, 10)  # wide enough for one digit (1.2) and not for two (2.4)
    assert _place(strip, digits=1).fits
    assert not _place(strip, digits=2).fits


def test_a_piece_that_is_too_small_does_not_fit_and_gets_the_number_at_its_centre():
    small = box(0, 0, 1, 1)
    placement = _place(small)
    assert not placement.fits
    assert (placement.x, placement.y) == pytest.approx((0.5, 0.5), abs=0.05)
    assert small.contains(box(placement.x, placement.y, placement.x, placement.y).centroid)


def test_a_mark_that_leaves_no_room_does_not_fit():
    square = box(0, 0, 4, 4)
    mark = ReferenceMark(2, 2, "circle", 3.5, 0.0)
    assert not _place(square, [mark]).fits


def test_the_number_of_a_c_shape_is_in_the_material_not_in_the_bay():
    c_shape = Polygon([(0, 0), (10, 0), (10, 3), (3, 3), (3, 7), (10, 7), (10, 10), (0, 10)])
    placement = _place(c_shape)
    b = number_box(placement.x, placement.y, digits=1, height=H, width_factor=W)
    assert placement.fits
    assert c_shape.contains(b)


@pytest.mark.parametrize("bad", [-1.0, float("nan"), float("inf")])
def test_a_bad_size_raises(bad):
    with pytest.raises(ValueError):
        place_number(box(0, 0, 10, 10), [], digits=1, height=bad, width_factor=W, clearance=0.0)


def test_the_clearance_can_decide_whether_the_number_fits():
    strip = box(0, 0, 10, 2.5)  # 2.5 tall: a number 2 tall fits, but not with 0.5 clear each side
    assert _place(strip, clearance=0.0).fits
    assert not _place(strip, clearance=0.5).fits


def _largest(contour, marks=(), *, digits=1, clearance=0.0, ceiling=5.0):
    return largest_fitting_height(
        contour, list(marks), digits=digits, ceiling=ceiling, width_factor=W, clearance=clearance
    )


def _fits(contour, marks, height, *, digits=1, clearance=0.0):
    return place_number(
        contour, list(marks), digits=digits, height=height, width_factor=W, clearance=clearance
    ).fits


def test_the_largest_fitting_height_of_a_square_is_its_side():
    square = box(0, 0, 4, 4)  # a box of height h is 0.6 h wide, so the height is the limit

    height = _largest(square)

    assert 3.9 <= height <= 4.0
    assert _fits(square, [], height)
    assert not _fits(square, [], height * 1.02)


def test_the_clearance_lowers_the_largest_fitting_height():
    square = box(0, 0, 4, 4)

    height = _largest(square, clearance=0.5)

    assert 2.9 <= height <= 3.0  # 4 - 2 x 0.5


def test_a_mark_lowers_the_largest_fitting_height():
    strip = box(0, 0, 20, 4)
    mark = ReferenceMark(10, 2, "circle", 2.0, 0.0)

    height = _largest(strip, [mark], ceiling=4.0)

    assert 0 < height < 4.0
    assert _fits(strip, [mark], height)
    assert not _fits(strip, [mark], height * 1.05)


def test_when_no_height_fits_the_largest_is_zero():
    square = box(0, 0, 4, 4)
    mark = ReferenceMark(2, 2, "circle", 6.0, 0.0)  # radius 3 covers the corners at 2.83

    assert _largest(square, [mark]) == 0.0


def test_a_height_that_already_fits_is_returned_as_it_is():
    assert _largest(box(0, 0, 40, 40), ceiling=5.0) == 5.0
