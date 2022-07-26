import os.path

from utils.api import create_response, create_error
from utils.characters.player_character import PlayerCharacter
from utils.characters.npc import NPC
import json
import math
import random


class GameController:
    CHARACTERS = ["manollo", "thork", "martha", "bart"]

    def __init__(self):
        self._og_x = 1000
        self._og_y = 683
        self._og_meter = 152.5 / 434
        self._pcs = {}
        self._allies = {}
        self._enemies = {}
        self._chars = {}
        self._round = 0
        self._queue = []
        self._full_queue = []
        self._load_characters()

    def start(self):
        int_rolls = []
        for pc in self._pcs:
            int_rolls.append(pc.int_roll())
            self._full_queue.append(pc)
        int_rolls, self._full_queue = zip(*sorted(zip(int_rolls, self._full_queue)))
        self._full_queue.append(self._allies)
        self._queue = self._full_queue.copy()
        self._round = 1
        return {"success": True, "msg": "", "data": {"first": self._queue.pop().get_name()}}

    def load_pc(self, character_name):

        # cache
        if character_name in self._pcs:
            return create_response(data=self._pcs[character_name])

        config_path = os.path.join("configs", character_name + ".json")
        if not os.path.isfile(config_path):
            return create_error(f"Config: '{config_path}' was not found")

        with open(config_path, "r") as reader:
            data = json.loads(reader.read())
            character = PlayerCharacter(data, data["name"])
            self._pcs[character_name] = character
            self._chars[character_name] = character
            return create_response(data=self._pcs[character_name])

    def create_npc(self, amount=20, allies=True):
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
                name = name + "_ally" if allies else + "_enemy"
                x = random.randint(0, self._og_x - 1)
                y = random.randint(0, self._og_y - 100)
                c = NPC(data, name, (x, y))
                if allies:
                    self._allies[name] = c
                else:
                    self._enemies[name] = c
                self._chars[name] = c
        return {"success": True, "msg": "", "data": {}}

    def get_all_characters(self):
        return self._chars

    def get_pcs(self):
        return self._pcs

    def get_allies(self):
        return self._allies

    def get_enemies(self):
        return self._enemies

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
        max_dist = r // self._og_meter
        dist = self._calc_distance((start_x, start_y), (dest_x, dest_y))
        if dist > max_dist:
            dest_x, dest_y = self._normalize_distance((start_x, start_y), (dest_x, dest_y), max_dist)
        response = []
        first_c = None
        first_dist = 0
        for c in self._chars:
            char_x, char_y = c.get_pos()
            x_dist = char_x - start_x
            y_dist = char_y - start_y
            if 0 < x_dist < 2 and 0 < y_dist < 2:
                continue
            cross = x_dist * dest_y - y_dist * dest_x
            char_dist = math.hypot(x_dist ** 2, y_dist ** 2)
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

    def _calc_distance(self, pos1, pos2):
        x_dist = pos1[0] - pos2[0]
        y_dist = pos1[0] - pos2[0]
        return math.hypot(x_dist ** 2, y_dist ** 2) * self._og_meter

    def _normalize_distance(self, pos1, pos2, max_dist):
        x_dir = pos1[0] - pos2[1]
        y_dir = pos1[1] - pos2[1]
        length = math.sqrt(x_dir ** 2 + y_dir ** 2)
        dest_x = int(max(min((x_dir / length) * max_dist, self._og_x), 0))
        dest_y = int(max(min((y_dir / length) * max_dist), self._og_y, 0))
        return dest_x, dest_y

    def attack(self, actor: str, target: str):
        pc = self._pcs[actor]
        tar = self._chars[target]
        if not pc.has_action():
            return create_error("No Action Points available")
        weapon = self._pcs[actor].get_active_weapon()
        resp = weapon.attack(self._calc_distance(pc.get_pos(), tar.get_pos()), self._chars[target])
        if resp["success"]:
            pc.use_action()
        return resp

    def move(self, target: str, pos, real_pixels):
        c = self._chars[target]
        max_dist = c.get_movement_left()
        new_pos = self._normalize_distance(c.get_pos, pos, max_dist)
        dist = math.ceil(self._calc_distance(c.get_pos, new_pos))
        c.move(new_pos, dist)
        x = self._og_x / real_pixels[0]
        y = self._og_y / real_pixels[1]
        x = round(x * new_pos[0])
        y = round(y * new_pos[1])
        return create_response({"x": x, "y": y})

    def _load_characters(self):
        for name in GameController.CHARACTERS:
            self.load_pc(name)

    def switch_weapon(self, name: str, target: str):
        character = self._chars.get(target, None)
        if character is None:
            return create_error("Character does not exist")
        if not character.has_action():
            return create_error("No Action Points available")
        weapon = character.switch_weapon(name)
        if weapon is None:
            return create_error("No suitable weapon found")
        character.use_action()
        return create_response(weapon)

    def change_health(self, target: str, life: int):
        c = self._chars.get(target, None)
        if c is None:
            return create_error("Character does not exist")
        c.change_health(life)
        return create_response(c)

    def stun(self, target: str):
        c = self._chars.get(target, None)
        if c is None:
            return create_error("Character does not exist")
        c.stun()
        return create_response(c)

