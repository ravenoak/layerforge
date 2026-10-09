"""The check before any file is written: do adjacent pieces align in exactly one way? (TR-2, TR-12)

For each pair of overlapping pieces in adjacent slices, the marks both slices hold must exist,
and no turn other than none may map them onto themselves (`rotation_symmetry`). A model of one
layer, and a piece that overlaps nothing, have no pair, so nothing is checked for them.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

from shapely.geometry import Point

from layerforge.models.reference_marks.config import require
from layerforge.models.reference_marks.symmetry import rotation_symmetry

from .adjacency import adjacent_pairs
from .slice import Slice

# `rotation_symmetry` refuses a tolerance of 0, and `--mark-tolerance 0` is allowed.
_MIN_SYMMETRY_TOLERANCE = 1e-6

Reason = Literal["no_shared_mark", "rotation_not_fixed"]


@dataclass(frozen=True)
class AlignmentFailure:
    """A pair of overlapping pieces that can be assembled in more than one way.

    Attributes
    ----------
    lower_slice, lower_piece : int
        The index of the lower slice and of the piece in it.
    upper_slice, upper_piece : int
        The index of the upper slice and of the piece in it.
    reason : {"no_shared_mark", "rotation_not_fixed"}
        ``no_shared_mark``: no mark is a hole in both pieces. ``rotation_not_fixed``: a turn
        other than none maps the shared marks onto themselves.
    """

    lower_slice: int
    lower_piece: int
    upper_slice: int
    upper_piece: int
    reason: Reason

    def message(self) -> str:
        """Return one line for the person: which pieces, what is wrong, what to try."""
        where = (
            f"slices {self.lower_slice} and {self.upper_slice} "
            f"(piece {self.lower_piece} and piece {self.upper_piece})"
        )
        if self.reason == "no_shared_mark":
            return (
                f"{where}: the pieces share no mark. Try a smaller --mark-min-distance or "
                "--mark-size (marks.min_distance or marks.size in the config file)."
            )
        return (
            f"{where}: the marks they share look the same after a turn, so the layers could be "
            "stacked turned. A circle or a square alone cannot fix the rotation. Allow a shape "
            "with a direction in --available-shapes (marks.shapes in the config file)."
        )


def check_alignment(slices: Sequence[Slice]) -> list[AlignmentFailure]:
    """Return every pair of adjacent pieces that does not align in exactly one way.

    The slices must already be adjusted (`SlicerService.slice_model` does that), because a mark
    that the adjuster dropped from either slice is not a hole in both pieces.

    Parameters
    ----------
    slices : Sequence of Slice
        The slices of one run, lowest first.

    Returns
    -------
    list of AlignmentFailure
        One per failing pair, lowest slice first. Empty when every pair aligns.
    """
    failures: list[AlignmentFailure] = []
    for lower, upper in zip(slices, slices[1:], strict=False):
        tolerance = max(require(lower.config.tolerance, "tolerance"), _MIN_SYMMETRY_TOLERANCE)
        boundary = adjacent_pairs(
            [lower.contours, upper.contours], min_overlap_area=lower.config.min_overlap_area
        )[0]
        for pair in boundary:
            lower_piece = lower.contours[pair.lower]
            upper_piece = upper.contours[pair.upper]
            shared = [
                mark
                for mark in lower.ref_marks
                if any(mark is other for other in upper.ref_marks)
                and lower_piece.contains(Point(mark.x, mark.y))
                and upper_piece.contains(Point(mark.x, mark.y))
            ]
            reason: Reason
            if not shared:
                reason = "no_shared_mark"
            elif rotation_symmetry(shared, tolerance=tolerance).has_nonidentity:
                reason = "rotation_not_fixed"
            else:
                continue
            failures.append(
                AlignmentFailure(lower.index, pair.lower, upper.index, pair.upper, reason)
            )
    return failures
