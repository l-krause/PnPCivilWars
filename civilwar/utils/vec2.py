import math

from utils.json_serializable import JsonSerializable


class Vector2D(JsonSerializable):
    def __init__(self, x, y):
        self._x = x
        self._y = y

    def __add__(self, v2):
        return Vector2D(self._x + v2[0], self._y + v2[1])

    def __sub__(self, v2):
        return Vector2D(self._x - v2[0], self._y - v2[1])

    def __mul__(self, a):
        return Vector2D(self._x * a, self._y * a)

    def __truediv__(self, a):
        return Vector2D(self._x / a, self._y / a)

    def length(self):
        return math.sqrt(self._x ** 2 + self._y ** 2)

    def normalize(self):
        length = self.length()
        if length > 0:
            return self / length
        return Vector2D(0, 0)

    def __getitem__(self, item):
        if item == 0:
            return self._x
        elif item == 1:
            return self._y
        raise IndexError()

    def __repr__(self):
        return f"vec({self._x}, {self._y})"

    def to_pos(self):
        from utils.position import Position
        return Position(self._x, self._y)

    @staticmethod
    def cross_multiply(v1, v2):
        return v1._x * v2._y - v1._y * v2._x

    def to_json(self):
        return {"x": self._x, "y": self._y}
