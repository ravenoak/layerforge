import pytest

from layerforge.models.slicing.slicer_service import SlicerService

@pytest.mark.parametrize("total_height,layer_height,expected", [
    (10, 3, [0, 3, 6, 9, 10]),
    (9, 3, [0, 3, 6, 9]),
    (5, 2, [0, 2, 4, 5]),
])
def test_calculate_slice_positions(total_height, layer_height, expected):
    positions = SlicerService.calculate_slice_positions(total_height, layer_height)
    assert positions == expected
    assert positions[-1] == total_height
