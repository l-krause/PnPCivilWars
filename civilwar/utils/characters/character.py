import logging
from abc import abstractmethod

from utils.api import create_error, ApiParameter
from utils.json_serializable import JsonSerializable


class Character(JsonSerializable, ApiParameter):

    def __init__(self, character_id, dictionary, pos=(0, 0)):
        self._id = character_id
        self._max_life = dictionary["lifePoints"]
        self._curr_life = dictionary["lifePoints"]
        self._armor = dictionary["armorClass"]
        self._movement = dictionary["movement"]
        self._movement_left = dictionary["movement"]
        self._passivePerception = dictionary["passivePerception"]
        self._active_weapon = dictionary["activeWeapon"]
        self._weapons = dictionary["weapons"]
        self._resistances = dictionary.get("resistance", [])
        self._token = dictionary.get("token", "")
        self._pos = pos
        self._action_points = 1
        self._stunned = False

    @abstractmethod
    def get_name(self):
        pass

    def get_armor(self):
        return self._armor

    def get_resistances(self):
        return self._resistances

    def get_pos(self):
        return self._pos

    def get_movement_left(self):
        return self._movement_left

    def save_roll(self, attribute: str):
        pass

    def get_active_weapon(self):
        return self._active_weapon

    def has_action(self):
        return self._action_points > 0

    def use_action(self):
        if not self.has_action():
            return False
        self._action_points -= 1
        return True

    def stun(self):
        self._stunned = not self._stunned

    def switch_weapon(self, name: str):
        for weapon in self._weapons:
            if name == weapon.get_name():
                self._active_weapon = weapon
                return weapon
        return None

    def change_health(self, health):
        tmp_health = self._curr_life + health
        if tmp_health > self._max_life:
            self._curr_life = self._max_life
            return
        if tmp_health <= self._max_life * -2:
            return
        self._curr_life = tmp_health

    def move(self, new_pos, dist):
        self._pos = new_pos
        self._movement_left -= dist

    def to_json(self):
        return {
            "id": self._id,
            "name": self.get_name(),
            "token": self._token,
            "pos": self._pos
        }

    def get_id(self):
        return self._id

    @staticmethod
    def api_validate(game_controller, value):
        if not isinstance(value, int):
            return create_error(f"Invalid type, required: int, got: {type(value)}")
        elif game_controller.get_character(value) is None:
            return create_error(f"No such character id={value}")

