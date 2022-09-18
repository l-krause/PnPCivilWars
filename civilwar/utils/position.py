from utils.api import ApiParameter, create_error


class Position(ApiParameter):

    def __init__(self, x, y):
        self._x = x
        self._y = y

    @staticmethod
    def api_validate(game_controller, value):
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
