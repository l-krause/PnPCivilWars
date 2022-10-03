import random
from abc import abstractmethod

from utils.api import create_error, ApiParameter
from utils.json_serializable import JsonSerializable
from utils.position import Position


class Character(JsonSerializable, ApiParameter):

    def __init__(self, character_id, dictionary, pos=Position(0, 0)):
        self._id = character_id
        self._max_life = dictionary["lifePoints"]
        self._curr_life = dictionary["lifePoints"]
        self._armor = dictionary["armorClass"]
        self._movement = dictionary["movement"]
        self._movement_left = dictionary["movement"] * 10
        self._passivePerception = dictionary["passivePerception"]
        self._active_weapon = dictionary["activeWeapon"]
        self._weapons = dictionary["weapons"]
        self._resistances = dictionary.get("resistance", [])
        self._std_resistances = dictionary.get("resistance", [])
        self._res_buff = 0
        self._token = dictionary.get("token", "")
        self._pos = pos
        self._action_points = 1
        self._action_points_max = 1
        self._ap_buff = 0
        self._stunned = 0
        self._death_advantage = False
        self._dead = False
        self._won_death = 0
        self._lost_death = 0
        self._spells = dictionary.get("spells", [])
        self._spell_slots = dictionary.get("spellSlots", [])
        self._available_slots = dictionary.get("spellSlots", [])

    @abstractmethod
    def get_name(self):
        pass

    def get_hp(self):
        return self._curr_life

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

    def stun(self, rounds):
        self._stunned += rounds

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
        self._movement_left = max(0, self._movement_left - dist)
        print("character.move(", new_pos, ",", dist, "), movement_left:", self._movement_left)

    def place(self, new_pos):
        self._pos = new_pos
        print("character.move(", new_pos, ")")

    def to_json(self):
        return {
            "id": self._id,
            "name": self.get_name(),
            "token": self._token,
            "pos": self._pos
        }

    def get_id(self):
        return self._id

    def turn_over(self):
        self._death_roll()
        self._movement_left = self._movement
        self._action_points = self._action_points_max
        if self._ap_buff > 0:
            self._ap_buff -= 1
            if self._ap_buff == 0:
                self._action_points_max = 1
        if self._res_buff > 0:
            self._res_buff -= 1
            if self._res_buff == 0:
                self._resistances = self._std_resistances.copy()

    def _death_roll(self):
        roll = random.randint(1, 20)
        if self._death_advantage:
            roll = max(roll, random.randint(1, 20))
        if roll > 10:
            if roll == 20:
                self._curr_life = 1
            else:
                self._won_death += 1
                if self._won_death == 3:
                    self._curr_life = random.randint(1, 4)
                    self._won_death = 0
                    self._lost_death = 0
        else:
            self._lost_death += 1
            if roll == 1:
                self._lost_death += 1
            if self._lost_death == 3:
                self._dead = True

    def is_dead(self):
        return self._dead

    @staticmethod
    def api_validate(game_controller, value):
        if not isinstance(value, int):
            return create_error(f"Invalid type, required: int, got: {type(value)}")

        character = game_controller.get_character(value)
        if character is None:
            return create_error(f"No such character id={value}")

        return character
