from characters.character import Character
import random
import math


class Spell:

    def __init__(self, dictionary):
        self._name = dictionary["name"]
        self._spell_type = dictionary["spellType"]
        self._usages = dictionary.get("usages", -1)
        self._dices = dictionary.get("dices", 0)
        self._dice_type = dictionary.get("diceType", 0)
        self._additional = dictionary.get("additional", 0)
        self._save = dictionary.get("save", 0)
        self._save_att = dictionary.get("saveAttribute", "")
        self._hit = dictionary.get("hit", 0)

    def cast(self, targets: list[Character], advantage: list[bool]):
        if self._usages == 0:
            return "No more usages"
        if self._usages > 0:
            self._usages -= 1
        response = []
        for i, target in enumerate(targets):
            if self._spell_type in "damage":
                response += self._damage_spell(target, advantage[i], )

    def _damage_spell(self, target: Character, advantage: bool, damage: int):
        hit = random.randint(1, 20) + self._hit
        hit2 = random.randint(1, 20) + self._hit
        hit = max(hit, hit2) if advantage else hit

        if hit < target.get_armor():
            return "Hit: " + hit, "Did not hit " + target.get_name()
        if self._save > 0:
            saved = target.save_roll(self._save_att)
            damage = damage if not saved else damage // 2
        target.change_health(damage)
        return "Hit for: " + hit, target.get_name() + "received " + str(damage) + " damage."

    def _roll(self):
        life_change = self._additional
        for i in range(self._dices):
            life_change += random.randint(self._dice_type)
        return life_change
