import random

from utils.api import ApiParameter, create_error
from utils.util import clamp
from utils.vec2 import Vector2D


class Position(Vector2D, ApiParameter):

    def __init__(self, x, y):
        super(Position, self).__init__(x, y)

    @staticmethod
    def api_validate(game_controller, value):
        if isinstance(value, Position):
            return value

        if isinstance(value, list):
            value = tuple(value)

        if not isinstance(value, tuple):
            return create_error(f"Invalid type, required: tuple, got: {type(value)}")
        elif len(value) != 2:
            return create_error(f"Expected a tuple of size 2, got {len(value)}")
        else:
            for index, comp in enumerate(value):
                if not isinstance(comp, (float, int)):
                    return create_error(f"Expected value at tuple index {index} to be int or float, got: {type(comp)}")

        return Position(value[0], value[1])

    @staticmethod
    def random(min_bounds, max_bounds):
        x = random.randint(min_bounds[0], max_bounds[0])
        y = random.randint(min_bounds[1], max_bounds[1])
        return Position(x, y)

    def distance(self, other_pos, factor=1.0):
        return len(other_pos - self) * factor

    def normalize_distance(self, other_pos, max_distance, max_bounds: Vector2D):
        direction = other_pos - self
        length = len(direction)
        print("dir:", dir, "length:", length)
        destination = ((direction / length) * max_distance).to_pos()
        return destination.to_bounds([0, 0], max_bounds)

    def to_bounds(self, min_bounds, max_bounds):
        self._x = clamp(self._x, min_bounds[0], max_bounds[0])
        self._y = clamp(self._y, min_bounds[1], max_bounds[1])

    def __repr__(self):
        return f"pos({self._x}, {self._y})"
