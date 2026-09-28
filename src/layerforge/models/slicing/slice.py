import logging

from shapely.geometry import Point, Polygon

from layerforge.models.reference_marks import (
    ReferenceMark,
    ReferenceMarkAdjuster,
    ReferenceMarkConfig,
)


class Slice:
    """Represents a single slice of a 3D model.

    Attributes
    ----------
    index : int
        The index of the slice in the model.
    position : float
        The Z position of the slice.
    contours : list
        A list of contours in the slice.
    ref_marks : List[ReferenceMark]
        The marks chosen for this slice by `plan_marks` (#63), before `adjust_marks` filters them.
    """

    def __init__(
        self,
        index: int,
        position: float,
        contours: list[Polygon],
        config: ReferenceMarkConfig | None = None,
        *,
        layer_height: float,
        ref_marks: list[ReferenceMark] | None = None,
        total_slices: int | None = None,
    ):
        """Initialize the slice.

        Parameters
        ----------
        index : int
            The index of the slice in the model.
        position : float
            The Z position of the slice.
        contours : list
            A list of contours in the slice.
        config : ReferenceMarkConfig, optional
            The mark settings. The slice resolves them with ``layer_height`` (TR-6, TR-10),
            so ``slice.config`` always holds a size, a minimum distance and a tolerance.
        layer_height : float
            The thickness of the layer (the sheet). It sets the least material between holes
            (``config.min_web_ratio`` times it).
        ref_marks : list of ReferenceMark, optional
            The marks `plan_marks` chose for this slice (#63). Empty when not given.
        total_slices : int, optional
            How many slices the whole run has. Only used to tell a single-slice model (which
            has no neighbour to align a mark to, so no size or distance change can help) apart
            from a multi-slice run in ``_warn_about_unmarked_contours``. ``None`` when unknown,
            which keeps the general multi-slice warning.
        """
        self.layer_height = layer_height
        self.contours = contours
        self.index = index
        self.config = (config or ReferenceMarkConfig()).resolved(layer_height)
        self.position = position
        self.ref_marks: list[ReferenceMark] = list(ref_marks) if ref_marks is not None else []
        self.total_slices = total_slices

    @property
    def min_web(self) -> float:
        """The least material between two holes, or between a hole and an outline."""
        return self.config.min_web_ratio * self.layer_height

    def adjust_marks(self) -> None:
        """Filter `ref_marks` to what actually fits this slice (TR-5), and warn if a piece has none.

        Returns
        -------
        None

        Raises
        ------
        ValueError
            If a mark names a shape that is not registered. The marks are left as they were.
        """
        self.ref_marks = ReferenceMarkAdjuster.adjust_marks(
            self.ref_marks, self.contours, config=self.config, min_web=self.min_web
        )
        self._warn_about_unmarked_contours()

    def _warn_about_unmarked_contours(self) -> None:
        """Log a warning if some contours of the slice ended up with no mark.

        A single-slice model has no adjacent layer to align a mark to at all (`plan_marks`
        needs a pair of layers), so no size or distance change can fix it; that case gets its
        own message instead of the generic one, which would be wrong advice there.
        """
        points = [Point(mark.x, mark.y) for mark in self.ref_marks]
        unmarked = [c for c in self.contours if not any(c.contains(p) for p in points)]
        if not unmarked:
            return
        if self.total_slices == 1:
            logging.warning(
                f"No reference mark fits {len(unmarked)} of {len(self.contours)} contours "
                f"in slice {self.index}. This model has only one layer; there is no "
                "neighbouring layer to align a mark to."
            )
        else:
            logging.warning(
                f"No reference mark fits {len(unmarked)} of {len(self.contours)} contours "
                f"in slice {self.index}. Try a smaller --mark-min-distance or --mark-size "
                "(marks.min_distance or marks.size in the config file)."
            )
