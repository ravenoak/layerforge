"""Choose the shape of a new mark by need (TR-8).

Every mark of a run has one angle, so a set of marks that holds one shape with a direction (a
symmetry order of 1) cannot be turned onto itself by any turn other than none. A circle or a
square cannot fix the rotation of a piece with one mark. The tool therefore prefers the shape
with the least symmetry, and the order of ``--available-shapes`` does not matter.
"""

import math
from collections.abc import Iterable

from layerforge.domain.shapes.registry import ShapeFactory, shape_symmetry_order


def choose_shape(available: Iterable[str]) -> str:
    """Return the shape a new mark should have, from the shapes the person allows.

    The shape with the lowest symmetry order comes first (a circle, which has none to count,
    comes last). Among shapes of one order, the one with the larger outline at one size wins,
    since a larger hole cuts cleaner in a thin sheet. A tie goes to the name that sorts first.

    Parameters
    ----------
    available : Iterable of str
        The names of the shapes that may be used.

    Returns
    -------
    str
        One of the names in ``available``.

    Raises
    ------
    ValueError
        If ``available`` is empty or names a shape that is not registered.
    """
    names = list(available)
    if not names:
        raise ValueError("choose_shape needs at least one shape")

    def need(name: str) -> tuple[float, float, str]:
        order = shape_symmetry_order(name)
        area = ShapeFactory.get_shape(name, 0.0, 0.0, 1.0).outline().area
        return (math.inf if order is None else order, -area, name)

    return min(names, key=need)
