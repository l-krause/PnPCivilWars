import random

from utils.api import create_response, create_error
from utils.constants import MEELE_RANGE, OG_METER


class Weapon:

    def __init__(self, dictionary):
        self._name = dictionary["name"]
        self._hit = dictionary["hit"]
        self._dices = dictionary["dices"]
        self._dice_type = dictionary["diceType"]
        self._type = dictionary["type"]
        self._additional = 0 if "additional" not in dictionary.keys() else dictionary["additional"]
        self._min_range = 0 if "minRange" not in dictionary.keys() else dictionary["minRange"]
        self._max_range = MEELE_RANGE if "maxRange" not in dictionary.keys() else dictionary["maxRange"]
        self._usages = -1 if "usages" not in dictionary.keys() else dictionary["usages"]

    def get_max_range(self):
        return self._max_range / OG_METER

    def is_ranged(self):
        return self._max_range > MEELE_RANGE

    def get_name(self):
        return self._name

    def attack(self, distance, target):
        if distance > self._max_range / OG_METER or distance < self._min_range / OG_METER:
            return create_error("Can't reach target")
        if self._usages == 0:
            return create_error("No ammo")
        if self._usages > 0:
            self._usages -= 1
        hit = random.randint(1, 20) + self._hit
        if hit < target.get_armor():
            return create_error(f"Missed target: {hit}")
        damage = self._additional
        for i in range(self._dices):
            damage += random.randint(1, self._dice_type)
        if self._type in target.get_resistances():
            damage = damage // 2

        target.change_health(-damage)
        return create_response({"hit": hit, "damage": damage, "target": target.get_id()})
