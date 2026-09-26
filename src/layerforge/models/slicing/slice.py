import logging

from shapely.geometry import Point, Polygon

from layerforge.models.reference_marks import (
    ReferenceMark,
    ReferenceMarkAdjuster,
    ReferenceMarkCalculator,
    ReferenceMarkConfig,
    ReferenceMarkManager,
)
from layerforge.models.reference_marks.config import require


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
        A list of reference marks in the slice.
    mark_manager : ReferenceMarkManager
        The reference mark manager for the slice.
    """

    def __init__(
        self,
        index: int,
        position: float,
        contours: list[Polygon],
        mark_manager: ReferenceMarkManager,
        config: ReferenceMarkConfig | None = None,
        *,
        layer_height: float,
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
        mark_manager : ReferenceMarkManager
            The reference mark manager for the slice.
        config : ReferenceMarkConfig, optional
            The mark settings. The slice resolves them with ``layer_height`` (TR-6, TR-10),
            so ``slice.config`` always holds a size, a minimum distance and a tolerance.
        layer_height : float
            The thickness of the layer (the sheet). It sets the default mark size and the
            least material between holes (``config.min_web_ratio`` times it).
        """
        self.layer_height = layer_height
        self.contours = contours
        self.index = index
        self.mark_manager = mark_manager
        self.config = (config or ReferenceMarkConfig()).resolved(layer_height)
        self.position = position

        self.ref_marks: list[ReferenceMark] = []

    @property
    def min_web(self) -> float:
        """The least material between two holes, or between a hole and an outline."""
        return self.config.min_web_ratio * self.layer_height

    def process_reference_marks(self) -> None:
        """Process reference marks for the slice.

        This method calculates potential reference marks, adjusts
        existing marks, and adds new marks. It uses the ReferenceMarkCalculator
        class.

        Returns
        -------
        None
        """
        tolerance = require(self.config.tolerance, "tolerance")
        size = require(self.config.size, "size")
        existing_positions = [(m.x, m.y) for m in self.mark_manager.marks]
        potential_marks = ReferenceMarkCalculator.get_stable_marks(
            self, existing_positions, config=self.config
        )
        for x, y in potential_marks:
            existing_mark = self.mark_manager.find_mark_by_position(x, y, tolerance=tolerance)
            if existing_mark:
                self.ref_marks.append(
                    ReferenceMark(
                        x=existing_mark.x,
                        y=existing_mark.y,
                        shape=existing_mark.shape,
                        size=existing_mark.size,
                        angle=existing_mark.angle,
                        color=existing_mark.color,
                    )
                )
            else:
                new_shape = self._select_unique_shape()
                self.mark_manager.add_or_update_mark(
                    x,
                    y,
                    new_shape,
                    size,
                    angle=self.config.angle,
                    color=self.config.color,
                    tolerance=tolerance,
                )
                self.ref_marks.append(
                    ReferenceMark(
                        x=x,
                        y=y,
                        shape=new_shape,
                        size=size,
                        angle=self.config.angle,
                        color=self.config.color,
                    )
                )

    def adjust_marks(self) -> None:
        """Adjust reference marks for the slice.

        This method adjusts reference marks based on the contours
        using the ReferenceMarkAdjuster class.

        Returns
        -------
        None

        Raises
        ------
        ValueError
            If a mark names a shape that is not registered. The marks are left as they were.
        """
        logging.debug(f"model_contours type: {type(self.contours)}, content: {self.contours}")
        self.ref_marks = ReferenceMarkAdjuster.adjust_marks(
            self.ref_marks, self.contours, config=self.config, min_web=self.min_web
        )
        self._warn_about_unmarked_contours()

    def _warn_about_unmarked_contours(self) -> None:
        """Log a warning if some contours of the slice ended up with no mark."""
        points = [Point(mark.x, mark.y) for mark in self.ref_marks]
        unmarked = [c for c in self.contours if not any(c.contains(p) for p in points)]
        if unmarked:
            logging.warning(
                f"No reference mark fits {len(unmarked)} of {len(self.contours)} contours "
                f"in slice {self.index}. Try a smaller --mark-min-distance or --mark-size."
            )

    def _select_unique_shape(self) -> str:
        """Select a unique shape for a reference mark.

        Returns
        -------
        str
            A unique shape for the reference mark.
        """
        available_shapes = self.config.available_shapes
        used_shapes = {mark.shape for mark in self.mark_manager.marks}
        for shape in available_shapes:
            if shape not in used_shapes:
                return shape
        return available_shapes[0]
