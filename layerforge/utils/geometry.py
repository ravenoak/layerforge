import logging

from shapely import Polygon, MultiPolygon


def calculate_distance(x1, y1, x2, y2):
    return ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5


def ensure_polygon(model_contours):
    try:
        if isinstance(model_contours, Polygon):
            return model_contours
        elif isinstance(model_contours, MultiPolygon):
            largest_polygon = max(model_contours, key=lambda p: p.area)
            return largest_polygon
        elif isinstance(model_contours, (list, tuple)):
            model_contours = [tuple(point) if isinstance(point, list) else point for point in model_contours]
            if all(isinstance(item, (list, tuple)) and len(item) == 2 for item in model_contours):
                return Polygon(model_contours)
        else:
            logging.debug(f"Unhandled model_contours type: {type(model_contours)}, content: {model_contours}")
    except Exception as e:
        logging.error(
            f"Failed to create a Polygon from model_contours: "
            f"{e}, type: {type(model_contours)}, content: {model_contours}")
        raise ValueError(f"Failed to create a Polygon from model_contours due to: {e}")
    raise ValueError("model_contours must be a Polygon object or a sequence of tuples suitable for Polygon creation.")
