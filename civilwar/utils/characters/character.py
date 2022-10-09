import random
from abc import abstractmethod, ABC

from utils.api import create_error, ApiParameter, create_response
from utils.constants import MEELE_RANGE, OG_METER
from utils.json_serializable import JsonSerializable
from utils.position import Position
from utils.util import clamp
from utils.weapon import Weapon


class Character(JsonSerializable, ApiParameter, ABC):

    def __init__(self, character_id, dictionary, pos=Position(0, 0)):
        self._id = character_id
        self._max_life = dictionary["lifePoints"]
        self._curr_life = dictionary["lifePoints"]
        self._armor = dictionary["armorClass"]
        self._movement = dictionary["movement"]
        self._movement_left = dictionary["movement"]
        self._passivePerception = dictionary["passivePerception"]
        self._weapons = [Weapon(weapon_data) for weapon_data in dictionary["weapons"]]
        self._active_weapon = self.get_weapon(dictionary["activeWeapon"])
        self._resistances = dictionary.get("resistance", [])
        self._std_resistances = dictionary.get("resistance", [])
        self._res_buff = 0
        self._token = dictionary.get("token", "")
        self._token_shadow = dictionary.get("tokenShadow", None)
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
        self.send_character_event("characterStunned", {"rounds": rounds})
        return create_response()

    def get_weapon(self, name: str):
        try:
            return next(filter(lambda w: w.get_name() == name, self._weapons))
        except StopIteration:
            return None

    def switch_weapon(self, weapon):
        if weapon not in self._weapons:
            return create_error("You do not own such weapon")
        elif not self.has_action():
            return create_error("No Action Points available")

        self._active_weapon = weapon
        self.use_action()
        self.send_character_event("characterSwitchWeapon", {"weapon": weapon})
        return create_response()

    def change_health(self, health):
        self._curr_life = clamp(health, -self._max_life, self._max_life)
        if self._curr_life == -self._max_life:
            self._dead = True

    def move(self, new_pos):
        dist = self._pos.distance(new_pos)
        self._pos = new_pos
        self._movement_left = max(0, self._movement_left - dist)
        self.send_character_event("characterMove", {"to": self._pos, "movementLeft": self._movement_left})
        return create_response()

    def place(self, new_pos: Position):
        from gamecontroller import GameController
        bounded_pos = new_pos.to_bounds(GameController.instance().get_map_bounds())
        self._pos = bounded_pos
        self.send_character_event("characterPlace", {"to": self._pos})
        return create_response()

    def get_status(self):
        if self.is_dead():
            return "dead"
        elif self.get_hp() <= 0:
            return "ko"
        else:
            return "alive"

    def to_json(self):
        data = {
            "id": self._id,
            "name": self.get_name(),
            "token": self._token,
            "pos": self._pos,
            "status": self.get_status(),
            "hp": self.get_hp(),
            "max_hp": self._max_life
        }

        if self._token_shadow:
            data["tokenShadow"] = self._token_shadow

        return data

    def get_id(self):
        return self._id

    def turn_over(self):
        if self.is_dead() or self.is_ko():
            return

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
        if self._stunned > 0:
            self._stunned -= 1

    def _death_roll(self):
        roll = random.randint(1, 20)
        if self._death_advantage:
            roll = max(roll, random.randint(1, 20))
        if roll > 10:
            if roll == 20:
                self.revive(reason="Nat 20")
            else:
                self._won_death += 1
                if self._won_death == 3:
                    self.revive(random.randint(1, 4), "Won 3 Death roles")
        else:
            self._lost_death += 1
            if roll == 1:
                self._lost_death += 1
            if self._lost_death == 3:
                self.kill(reason="Death Roll")

    def is_dead(self):
        return self._dead

    def is_ko(self):
        return not self.is_dead() and self._curr_life <= 0

    def kill(self, reason=None):
        self._dead = True
        from gamecontroller import GameController
        GameController.instance().on_character_died(self, reason=reason)

    def revive(self, hp=1, reason=None):
        self._won_death = 0
        self._lost_death = 0
        self._curr_life = hp
        self._dead = False
        self.send_character_event("characterSurvived", data={"reason": reason, "hp": self.get_hp()})

    @staticmethod
    def api_validate(game_controller, value):
        if not isinstance(value, int):
            return create_error(f"Invalid type, required: int, got: {type(value)}")

        character = game_controller.get_character(value)
        if character is None:
            return create_error(f"No such character id={value}")

        return character

    def get_enemies_with_distance(self, distance=MEELE_RANGE/OG_METER):
        from gamecontroller import GameController
        game_controller = GameController.instance()
        filters = [
            lambda c: not c.is_dead(),  # character is alive
            lambda c: self.distance(c) <= distance,  # in range
            lambda c: not self.is_allied_to(c),  # is not allied to
        ]

        return game_controller.get_characters_by(*filters)

    def get_closest_enemy(self):
        from gamecontroller import GameController
        game_controller = GameController.instance()
        enemies = list(game_controller.get_characters_by(lambda c: not c.is_dead() and not self.is_allied_to(c)))
        if len(enemies) == 0:
            return None

        closest_enemy = enemies[0]
        closest_dist = self.distance(closest_enemy)
        for enemy in enemies:
            dist = self.distance(enemy)
            if dist < closest_dist:
                closest_enemy = enemy
                closest_dist = dist

        return closest_enemy

    @abstractmethod
    def is_allied_to(self, other):
        pass

    def distance(self, other, factor=1.0):
        return self.get_pos().distance(other.get_pos(), factor)

    def move_towards(self, other, requested_distance):
        from gamecontroller import GameController
        game_controller = GameController.instance()
        current_distance = self.distance(other, OG_METER)
        move_distance = min(current_distance - requested_distance, self._movement_left)
        if move_distance > 0:
            target_pos = self.get_pos().normalize_distance(other.get_pos(), move_distance / OG_METER,
                                                           game_controller.get_map_bounds())
            self.move(target_pos)

    def get_ranged_weapon(self):
        try:
            return next(filter(lambda w: w.is_ranged(), self._weapons))
        except StopIteration:
            return None

    def send_character_event(self, event, data=None):
        data = {} if data is None else data
        data["characterId"] = self._id
        from gamecontroller import GameController
        GameController.instance().send_game_event(event, data)

    def __repr__(self):
        is_dead = ", dead" if self.is_dead() else ""
        return f"{type(self).__name__}(id={self._id}, name={self.get_name()}, hp={self._curr_life}/{self._max_life}{is_dead})"
