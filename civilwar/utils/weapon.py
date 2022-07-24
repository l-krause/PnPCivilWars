from characters.character import Character
import random


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

    def attack(self, pos, target: Character):
        distance = target.calc_distance(pos)
        if distance > self._max_range or distance < self._min_range:
            print("Can't reach target")
            return
        if self._usages == 0:
            print("Can't attack")
            return
        if self._usages > 0:
            self._usages -= 1
        hit = random.randint(1, 20) + self._hit
        print(hit)
        if hit < target.get_armor():
            print("Missed")
            return
        damage = self._additional
        for i in range(self._dices):
            damage += random.randint(1, self._dice_type)
        if self._type in target.get_resistances():
            damage = damage // 2
        damage *= -1
        print("Damage " + str(damage))
        target.change_health(damage)