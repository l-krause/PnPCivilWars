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
        elif isinstance(value, dict):
            if set(value.keys()) != {"x", "y"}:
                return create_error(f"Expected dict to have keys: x, y, got: {list(value.keys())}")
            for key in ["x", "y"]:
                prop = value[key]
                if not isinstance(prop, (float, int)):
                    return create_error(f"Expected dict to have property '{key}' to be int or float, got: {type(prop)}")
            return Position(value["x"], value["y"])

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
        return (other_pos - self).length() * factor

    def normalize_distance(self, other_pos, max_distance, bounds: Vector2D):
        dir_vector = (other_pos - self).normalize()
        destination = (self + (dir_vector * max_distance)).to_pos()
        return destination.to_bounds(bounds)

    def to_bounds(self, bounds):
        # bounds: [min_x, min_y, max_x, max_y]
        x = clamp(self._x, bounds[0], bounds[2])
        y = clamp(self._y, bounds[1], bounds[3])
        return Position(x, y)

    def __repr__(self):
        return f"pos({self._x}, {self._y})"
