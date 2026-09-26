import math

import pytest

pytest.importorskip("trimesh")
pytest.importorskip("shapely")
from layerforge.models.reference_marks import (
    ReferenceMark,
    ReferenceMarkConfig,
    ReferenceMarkManager,
)


def test_add_and_update_mark():
    manager = ReferenceMarkManager()
    manager.add_or_update_mark(10, 20, "circle", 3, angle=math.pi / 4, color="red")
    assert len(manager.marks) == 1
    assert manager.marks[0].shape == "circle"
    assert manager.marks[0].size == 3
    assert manager.marks[0].angle == math.pi / 4
    assert manager.marks[0].color == "red"

    # update existing position
    manager.add_or_update_mark(10, 20, "square", 5, angle=math.pi / 2, color="blue")
    assert len(manager.marks) == 1
    assert manager.marks[0].shape == "square"
    assert manager.marks[0].size == 5
    assert manager.marks[0].angle == math.pi / 2
    assert manager.marks[0].color == "blue"

    # add new mark at different position
    manager.add_or_update_mark(30, 40, "triangle", 4)
    assert len(manager.marks) == 2


def _manager_with(*marks: tuple[float, float, str]) -> ReferenceMarkManager:
    """A manager holding marks at the given places, whatever their spacing."""
    manager = ReferenceMarkManager()
    manager.marks = [ReferenceMark(x=x, y=y, shape=shape, size=3) for x, y, shape in marks]
    return manager


def test_find_mark_by_position_returns_the_nearest_mark_in_range():
    manager = _manager_with((0, 0, "circle"), (8, 0, "square"))

    found = manager.find_mark_by_position(6, 0, tolerance=10)

    assert found is not None
    assert (found.x, found.y, found.shape) == (8, 0, "square")


def test_find_mark_by_position_breaks_a_tie_with_the_earliest_mark():
    manager = _manager_with((0, 0, "circle"), (10, 0, "square"))

    found = manager.find_mark_by_position(5, 0, tolerance=10)

    assert found is not None
    assert found.shape == "circle"


def test_find_mark_by_position_ignores_marks_out_of_range():
    manager = _manager_with((0, 0, "circle"))

    assert manager.find_mark_by_position(11, 0, tolerance=10) is None


def test_add_or_update_mark_updates_the_nearest_mark():
    manager = _manager_with((0, 0, "circle"), (8, 0, "square"))

    manager.add_or_update_mark(7, 0, "triangle", 4)

    assert [m.shape for m in manager.marks] == ["circle", "triangle"]


def test_add_or_update_mark_uses_the_tolerance_it_is_given():
    """#108 item 1: the caller's tolerance replaces the manager's own."""
    manager = ReferenceMarkManager(config=ReferenceMarkConfig(tolerance=40))
    manager.add_or_update_mark(0, 30, "square", 3)

    manager.add_or_update_mark(0, 0, "circle", 3, tolerance=0.3)
    assert [(m.shape, m.y) for m in manager.marks] == [("square", 30), ("circle", 0)]

    manager.add_or_update_mark(0, 0.2, "triangle", 4, tolerance=0.3)
    assert [(m.shape, m.y) for m in manager.marks] == [("square", 30), ("triangle", 0)]
