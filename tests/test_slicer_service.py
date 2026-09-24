import pytest

pytest.importorskip("trimesh")

from layerforge.models.slicing.slicer_service import SlicerService


@pytest.mark.parametrize(
    "bottom,top,layer_height,expected",
    [
        (0, 10, 3, [1.5, 4.5, 7.5, 9.5]),
        (0, 9, 3, [1.5, 4.5, 7.5]),
        (0, 5, 2, [1, 3, 4.5]),
        # A mesh centred on z=0 is sliced over its whole height.
        (-10, 10, 5, [-7.5, -2.5, 2.5, 7.5]),
        (4, 10, 3, [5.5, 8.5]),
        # A layer taller than the model still gives one slice.
        (0, 2, 5, [1]),
        # Float noise must not add a sliver layer: 0.3 / 0.1 is 2.9999999999999996.
        (0, 0.3, 0.1, [0.05, 0.15, 0.25]),
    ],
)
def test_calculate_slice_positions(bottom, top, layer_height, expected):
    positions = SlicerService.calculate_slice_positions(bottom, top, layer_height)
    assert positions == pytest.approx(expected)


@pytest.mark.parametrize("bottom,top,layer_height", [(0, 20, 5), (-3, 7.7, 2), (5, 5.5, 1)])
def test_positions_stay_strictly_inside_the_model(bottom, top, layer_height):
    """A cut on the top or bottom face is coplanar with it and comes out empty."""
    positions = SlicerService.calculate_slice_positions(bottom, top, layer_height)
    assert all(bottom < p < top for p in positions)
