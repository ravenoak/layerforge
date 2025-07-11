from typing import List
import math

from layerforge.models import Slice, Model
from layerforge.models.reference_marks import (
    ReferenceMarkManager,
    ReferenceMarkConfig,
    ReferenceMarkService,
)


class SlicerService:
    """Service class for slicing models"""
    @staticmethod
    def calculate_slice_positions(total_height: float, layer_height: float) -> list[float]:
        """Calculate the positions of the slices

        Parameters
        ----------
        total_height : float
            The total height of the model
        layer_height : float
            The height of each layer

        Returns
        -------
        list
            A list of the positions of the slices
        """
        num_slices = max(1, math.ceil(total_height / layer_height))
        positions = [i * layer_height for i in range(num_slices)]
        if not positions or positions[-1] < total_height:
            positions.append(total_height)
        else:
            positions[-1] = total_height
        return positions

    @staticmethod
    def slice_model(
        model: Model, config: ReferenceMarkConfig | None = None
    ) -> list[Slice]:
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
        cfg = config or ReferenceMarkConfig()
        slice_positions = SlicerService.calculate_slice_positions(
            model.calculate_height(), model.layer_height
        )
        slices = []
        mark_manager = ReferenceMarkManager(config=cfg)
        for index, position in enumerate(slice_positions):
            contours = model.calculate_slice_contours(position)
            slice_ = Slice(
                index=index,
                position=position,
                contours=contours,
                origin=model.origin,
                mark_manager=mark_manager,
                config=cfg,
            )
            # Process and adjust reference marks outside of the slicing logic
            ReferenceMarkService.process_slice(slice_)
            slices.append(slice_)
        return slices
