import logging
import math

from layerforge.models import Model, Slice
from layerforge.models.reference_marks import ReferenceMarkConfig
from layerforge.models.reference_marks.pair_marking import plan_marks


class SlicerService:
    """Service class for slicing models"""

    @staticmethod
    def calculate_slice_positions(bottom: float, top: float, layer_height: float) -> list[float]:
        """Calculate the positions of the slices

        The model is divided into layers of ``layer_height`` from ``bottom``
        upwards. The last layer is shorter if the height is not a multiple of
        ``layer_height``. Each slice is cut at the middle of its layer, so a cut
        never lies on the bottom or top face.

        Parameters
        ----------
        bottom : float
            The lowest z of the model
        top : float
            The highest z of the model
        layer_height : float
            The height of each layer

        Returns
        -------
        list
            A list of the z positions of the slices, lowest first
        """
        # Rounding stops float noise (0.3 / 0.1 is 2.9999999999999996) from
        # adding a sliver layer.
        num_slices = max(1, math.ceil(round((top - bottom) / layer_height, 9)))
        positions: list[float] = []
        for i in range(num_slices):
            lower = bottom + i * layer_height
            upper = min(lower + layer_height, top)
            positions.append((lower + upper) / 2)
        return positions

    @staticmethod
    def slice_model(model: Model, config: ReferenceMarkConfig | None = None) -> list[Slice]:
        """Slice the model into layers

        Parameters
        ----------
        model : Model
            The model to slice

        Returns
        -------
        List[Slice]
            A list of the slices
        """
        # Resolve once: every slice and plan_marks then share one size, one minimum distance
        # and one snapping tolerance (TR-6, TR-10, #108).
        cfg = (config or ReferenceMarkConfig()).resolved(model.layer_height)
        least = cfg.min_size(model.layer_height)
        if cfg.size is not None and cfg.size < least:
            logging.warning(
                f"The mark size {cfg.size:g} is below the least hole size {least:g} for a sheet "
                f"of {model.layer_height:g} and a kerf of {cfg.kerf:g}. "
                "Holes this small may not cut cleanly."
            )
        min_bound, max_bound = model.mesh.bounds
        slice_positions = SlicerService.calculate_slice_positions(
            float(min_bound[2]), float(max_bound[2]), model.layer_height
        )
        contours = [model.calculate_slice_contours(p) for p in slice_positions]
        marks = plan_marks(contours, cfg, model.layer_height)
        slices = [
            Slice(
                index=i,
                position=p,
                contours=c,
                config=cfg,
                layer_height=model.layer_height,
                ref_marks=m,
                total_slices=len(slice_positions),
            )
            for i, (p, c, m) in enumerate(zip(slice_positions, contours, marks, strict=True))
        ]
        for slice_ in slices:
            slice_.adjust_marks()
        return slices
