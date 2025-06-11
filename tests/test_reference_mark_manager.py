import pytest
pytest.importorskip("trimesh")
pytest.importorskip("shapely")
from layerforge.models.reference_marks import ReferenceMarkManager, ReferenceMark


def test_add_and_update_mark():
    manager = ReferenceMarkManager()
    manager.add_or_update_mark(10, 20, "circle", 3, angle=45, color="red")
    assert len(manager.marks) == 1
    assert manager.marks[0].shape == "circle"
    assert manager.marks[0].size == 3
    assert manager.marks[0].angle == 45
    assert manager.marks[0].color == "red"

    # update existing position
    manager.add_or_update_mark(10, 20, "square", 5, angle=90, color="blue")
    assert len(manager.marks) == 1
    assert manager.marks[0].shape == "square"
    assert manager.marks[0].size == 5
    assert manager.marks[0].angle == 90
    assert manager.marks[0].color == "blue"

    # add new mark at different position
    manager.add_or_update_mark(30, 40, "triangle", 4)
    assert len(manager.marks) == 2
