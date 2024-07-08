class ReferenceMarkManager:
    def __init__(self):
        self.marks = []  # Each mark is a dict with keys: x, y, shape, size

    def find_mark_by_position(self, x, y, tolerance=10):
        for mark in self.marks:
            distance = ((x - mark['x'])**2 + (y - mark['y'])**2)**0.5
            if distance <= tolerance:
                return mark
        return None

    def add_or_update_mark(self, x, y, shape, size):
        mark = self.find_mark_by_position(x, y)
        if mark:
            # Update existing mark if it's within tolerance
            mark['shape'] = shape
            mark['size'] = size
        else:
            # Add a new mark if no existing mark is found within tolerance
            self.marks.append({'x': x, 'y': y, 'shape': shape, 'size': size})
