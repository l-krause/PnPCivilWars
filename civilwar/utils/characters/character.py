import json
from abc import ABC, abstractmethod


class Character(ABC):

    def __init__(self, dictionary):
        self._max_life = dictionary["lifePoints"]
        self._curr_life = dictionary["lifePoints"]
        self._armor = dictionary["armorClass"]
        self._movement = dictionary["movement"]
        self._movement_left = dictionary["movement"]
        self._passivePerception = dictionary["passivePerception"]
        self._active_weapon = dictionary["activeWeapon"]
        self._weapons = dictionary["weapons"]
        self._resistances = [] if "resistances" not in dictionary.keys() else dictionary["resistance"]
        self._pos = (0, 0)
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

    def switch_weapon(self, name: str):
        for weapon in self._weapons:
            if name == weapon.get_name():
                self._active_weapon = weapon
                return

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
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)
