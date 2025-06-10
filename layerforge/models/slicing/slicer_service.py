from typing import List

from layerforge.models import Slice, Model
from layerforge.models.reference_marks import ReferenceMarkManager, ReferenceMarkConfig


class SlicerService:
    """Service class for slicing models"""
    @staticmethod
    def calculate_slice_positions(total_height: float, layer_height: float) -> list:
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
        return [i * layer_height for i in range(int(total_height / layer_height) + 1)]

    @staticmethod
    def slice_model(
        model: Model, config: ReferenceMarkConfig | None = None
    ) -> List[Slice]:
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
            # TODO: Investigate if this is the best place to process the reference marks
            slice_.process_reference_marks()
            slice_.adjust_marks()
            slices.append(slice_)
        return slices
