from layerforge.domain.shapes import Circle, Square, Triangle, Arrow


class ShapeFactory:
    @staticmethod
    def get_shape(shape_type, *args, **kwargs):
        if shape_type == 'circle':
            return Circle(*args, **kwargs)
        elif shape_type == 'square':
            return Square(*args, **kwargs)
        elif shape_type == 'triangle':
            return Triangle(*args, **kwargs)
        elif shape_type == 'arrow':
            return Arrow(*args, **kwargs)
        else:
            raise ValueError(f"Unknown shape type: {shape_type}")
