from utils.api import ApiParameter, create_error
from utils.json_serializable import JsonSerializable


class CharacterStats(ApiParameter, JsonSerializable):

    def __init__(self, curr_hp, max_hp, armor, dice, damage, modifier):
        self.curr_hp = curr_hp
        self.max_hp = max_hp
        self.dice = dice

        # weapon stats
        self._affected_weapon = None
        self.damage = damage
        self.modifier = modifier
        self.armor = armor

    def to_json(self):
        pass

    @staticmethod
    def api_validate(game_controller, value):
        if isinstance(value, CharacterStats):
            return value

        if not isinstance(value, dict):
            return create_error(f"Invalid type, required: dict, got: {type(value)}")

        constructor_args = []
        attributes = ["curr_hp", "max_hp", "armor", "dice", "damage", "modifier"]
        for attr in attributes:
            if attr not in value:
                return create_error(f"CharacterStats dict missing required attribute: '{attr}'")
            elif not isinstance(value[attr], int):
                return create_error(f"CharacterStats attribute '{attr}' has wrong type, expected=int got={type(value['attr'])}")
            else:
                constructor_args.append(value[attr])

        return CharacterStats(*constructor_args)

