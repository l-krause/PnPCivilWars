from .character import Character
import random


class PlayerCharacter(Character):

    def __init__(self, character_id, dictionary):
        super().__init__(character_id, dictionary)
        self._name = dictionary["name"]
        self.is_online = True
        self._initiative = dictionary.get("initiative", 0)

    def get_name(self):
        return self._name

    def int_roll(self):
        roll = random.randint(1, 20) + self._initiative
        return roll

    def to_json(self):
        data = super().to_json()
        data["type"] = "player"
        return data
