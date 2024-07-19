from layerforge.models import Slice
from layerforge.models.reference_marks import ReferenceMarkManager


class SlicerService:
    @staticmethod
    def calculate_slice_positions(total_height, layer_height):
        return [i * layer_height for i in range(int(total_height / layer_height) + 1)]

    @staticmethod
    def slice_model(model):
        slice_positions = SlicerService.calculate_slice_positions(model.calculate_height(), model.layer_height)
        slices = []
        mark_manager = ReferenceMarkManager()
        for index, position in enumerate(slice_positions):
            contours = model.calculate_slice_contours(position)
            slice_ = Slice(index=index, position=position, contours=contours, origin=model.origin,
                           mark_manager=mark_manager)
            slice_.process_reference_marks()
            slice_.adjust_marks()
            slices.append(slice_)
        return slices
