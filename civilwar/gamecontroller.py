from utils.characters.character import Character
from utils.characters.player_character import PlayerCharacter
from utils.characters.npc import NPC
import json
import math


class GameController:

    def __init__(self):
        self._og_x = 1000
        self._og_y = 683
        self._og_meter = 152.5 / 434
        self._pcs = []
        self._allies = []
        self._enemies = []
        self._chars = []

    def create_pc(self, config_path):
        name = config_path.split("/")[1].replace(".json", "")
        for c in self._pcs:
            if name in c.get_name().tolower():
                return {"success": False, "msg": "Config: " + config_path + "was not found", "data": {}}
        with open(config_path, "r") as reader:
            data = reader.read()
            data = json.loads(data)
            character = PlayerCharacter(data, data["name"])
            self._pcs += [character]
            self._chars += [character]
            return {"success": True, "msg": "", "data": data}

    def create_allies(self, amount=20):
        villager = "configs/villager.json"
        veteran = "configs/veteran.json"
        for i in range(amount):
            conf = villager
            if i % 5 == 0:
                conf = veteran
            with open(conf, "r") as reader:
                data = reader.read()
                data = json.loads(data)
                name = data["name"] + str(len(self._allies))
                c = NPC(data, name, )
                self._allies += [c]


    def get_characters_aoe(self, start_pos, r, real_pixels):
        x = self._og_x / real_pixels[0]
        y = self._og_y / real_pixels[1]
        start_x = round(start_pos[0] * x)
        start_y = round(start_pos[1] * y)
        pixel_dist = r // self._og_meter
        response = []
        for c in self._chars:
            char_x, char_y = c.get_pos()
            x_dist = char_x - start_x
            y_dist = char_y - start_y
            if 0 < x_dist < 2 and 0 < y_dist < 2:
                continue
            if x_dist ** 2 + y_dist ** 2 <= pixel_dist:
                response += [c]
        return response

    def get_characters_line(self, start_pos, dest_pos, r, real_pixels, pierce=True):
        x = self._og_x / real_pixels[0]
        y = self._og_y / real_pixels[1]
        start_x = round(start_pos[0] * x)
        start_y = round(start_pos[1] * y)
        dest_x = round(dest_pos[0] * x)
        dest_y = round(dest_pos[1] * y)
        dist = r // self._og_meter
        while True:
            x_dist = start_x - dest_x
            y_dist = start_y - dest_y
            if x_dist ** 2 + y_dist ** 2 <= dist:
                break
            dest_x -= 1
            dest_y -= 1
        response = []
        first_c = None
        first_dist = 0
        for c in self._chars:
            char_x, char_y = c.get_pos()
            x_dist = char_x - start_x
            y_dist = char_y - start_y
            if 0 < x_dist < 2 and 0 < y_dist < 2:
                continue
            cross = x_dist * start_y - y_dist * start_x
            char_dist = math.hypot(x_dist**2, y_dist**2)
            if cross > 3 or char_dist > dist:
                continue
            if pierce:
                response += [c]
            else:
                if first_c is None:
                    first_c = c
                    first_dist = char_dist
                else:
                    if first_dist > char_dist:
                        first_c = c
                        first_dist = char_dist
        if not pierce and first_c is not None:
            response += [first_c]
        return response