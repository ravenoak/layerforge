from layerforge.models.slicing.slice import Slice
from layerforge.models.reference_marks import ReferenceMarkManager, ReferenceMarkConfig


def _make_slice(origin=(0, 0)) -> Slice:
    manager = ReferenceMarkManager()
    cfg = ReferenceMarkConfig()
    return Slice(0, 0.0, [], origin=origin, mark_manager=manager, config=cfg)


def test_mark_size_ranges():
    sl = _make_slice()
    coords = [
        (0, 0, 3),
        (15, 0, 3),
        (35, 0, 3),
        (40, 0, 4),
        (50, 0, 5),
        (100, 0, 5),
        (70, 70, 5),
    ]
    for x, y, expected in coords:
        size = sl._calculate_mark_size(x, y)
        assert 3 <= size <= 5
        assert size == expected
