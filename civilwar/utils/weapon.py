from characters.character import Character
import random

from utils.api import create_response


class Weapon:

    def __init__(self, dictionary):
        self._name = dictionary["name"]
        self._hit = dictionary["hit"]
        self._dices = dictionary["dices"]
        self._dice_type = dictionary["diceType"]
        self._type = dictionary["type"]
        self._additional = 0 if "additional" not in dictionary.keys() else dictionary["additional"]
        self._min_range = 0 if "min_range" not in dictionary.keys() else dictionary["min_range"]
        self._max_range = 1.5 if "max_range" not in dictionary.keys() else dictionary["max_range"]
        self._usages = -1 if "usages" not in dictionary.keys() else dictionary["usages"]

    def get_name(self):
        return self._name

    def attack(self, distance, target: Character):
        if distance > self._max_range or distance < self._min_range:
            return {"success": False, "msg": "Can't reach target", "data": {}}
        if self._usages == 0:
            return {"success": False, "msg": "No ammo", "data": {}}
        if self._usages > 0:
            self._usages -= 1
        hit = random.randint(1, 20) + self._hit
        print(hit)
        if hit < target.get_armor():
            return {"success": False, "msg": "Missed target: " + str(hit), "data": {}}
        damage = self._additional
        for i in range(self._dices):
            damage += random.randint(1, self._dice_type)
        if self._type in target.get_resistances():
            damage = damage // 2
        damage *= -1
        target.change_health(damage)
        return create_response({"hit": "Hit for " + str(hit), "damage": str(damage) + " damage", "target": target.get_id()})
