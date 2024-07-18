from shapely.geometry import Point, Polygon


class ReferenceMarkAdjuster:
    @staticmethod
    def adjust_marks(marks, model_polygon, min_distance=10):
        if not isinstance(model_polygon, Polygon):
            raise TypeError("model_polygon must be a shapely.geometry.Polygon object")

        adjusted_marks = []
        for mark in marks:
            mark_point = Point(mark[0], mark[1])
            if model_polygon.distance(mark_point) < min_distance:
                continue
            is_overlapping = False
            for adj_mark in adjusted_marks:
                adj_mark_point = Point(adj_mark[0], adj_mark[1])
                if mark_point.distance(adj_mark_point) < min_distance:
                    is_overlapping = True
                    break
            if not is_overlapping:
                adjusted_marks.append(mark)
        return adjusted_marks
