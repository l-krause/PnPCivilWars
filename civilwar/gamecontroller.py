from utils.characters.character import Character
from utils.characters.player_character import PlayerCharacter
import json


class GameController:

    def __init__(self):
        self._pcs = []
        self._allies = []
        self._enemies = []

    def create_pc(self, config_path):
        name = config_path.split("/")[1].replace(".json", "")
        for c in self._pcs:
            if name in c.get_name().tolower():
                return
        with open(config_path, "r") as reader:
            data = reader.read()
            data = json.loads(data)
            character = PlayerCharacter(data)
            self._pcs += [character]
