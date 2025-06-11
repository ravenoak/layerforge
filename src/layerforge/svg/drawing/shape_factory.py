from src.layerforge.domain.shapes import Circle, Square, Triangle, Arrow


class ShapeFactory:
    """Factory class for creating shapes."""
    @staticmethod
    def get_shape(shape_type: str, *args, **kwargs) -> object:
        """Return a shape object based on the shape type.

        Parameters
        ----------
        shape_type : str
            The type of shape to create.
        """
        # TODO: Research type hints for return value and BaseShape
        # TODO: Update docstring after refactoring out args and kwargs
        # TODO: Update this to use a registry of shape types
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
