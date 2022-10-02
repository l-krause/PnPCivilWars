import json
import logging
import math
import os.path
import random

from utils.api import create_response, create_error
from utils.characters.character import Character
from utils.characters.npc import NPC
from utils.characters.player_character import PlayerCharacter


class GameController:

    _instance = None

    CHARACTER_ID = 1

    def __init__(self):
        self._og_x = 1000
        self._og_y = 683
        self._og_meter = 152.5 / 434
        self._pcs = {}
        self._dead_pcs = {}
        self._allies = {}
        self._ko_allies = {}
        self._dead_allies = {}
        self._enemies = {}
        self._ko_enemies = {}
        self._dead_enemies = {}
        self._chars = {}
        self._round = 0
        self._queue = []
        self._full_queue = []
        self._character_configs = {}
        self._load_character_configs()
        self._active_char = None

    def next_char_id(self):
        next_id = self.CHARACTER_ID
        self.CHARACTER_ID += 1
        return next_id

    def start(self):
        int_rolls = []
        for pc in self._pcs:
            int_rolls.append(pc.int_roll())
            self._full_queue.append(pc)
        int_rolls, self._full_queue = zip(*sorted(zip(int_rolls, self._full_queue)))
        self._full_queue.append(self._allies)
        self._queue = self._full_queue.copy()
        self._round = 1
        self._active_char = self._queue.pop()
        return create_response({"first": self._active_char.get_id()})

    def create_npc(self, amount=20, allies=True):
        villager_config = self._character_configs["villager"]
        veteran_config = self._character_configs["veteran"]
        for i in range(amount):
            character_config = (veteran_config if i % 5 == 0 else villager_config).copy()
            x = random.randint(0, self._og_x - 1)
            y = random.randint(0, self._og_y - 100)
            name = character_config["name"] + str(len(self._allies)) + ("_ally" if allies else "_enemy")
            character_id = self.next_char_id()
            npc = NPC(character_id, character_config, name, (x, y))
            if allies:
                self._allies[character_id] = npc
            else:
                self._enemies[character_id] = npc
            self._chars[character_id] = npc
        return True

    def create_pc(self, character_name):
        logging.debug("GameController.create_pc")
        character_config = self._character_configs.get(character_name, None)
        if not character_config:
            return create_error(f"Invalid character: {character_name}")
        elif character_config["type"] != "player":
            return create_error(f"Chosen character is not a playable character")

        character_id = self.next_char_id()
        character = PlayerCharacter(character_id, character_config)
        self._pcs[character_id] = character
        self._chars[character_id] = character
        return character

    def get_all_characters(self):
        return self._chars

    def get_pcs(self):
        return self._pcs

    def get_allies(self):
        return self._allies

    def get_enemies(self):
        return self._enemies

    def get_character(self, character_id):
        if character_id is None:
            return None
        return self._chars.get(character_id, None)

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
        print("_normalize_distance pos1=", pos1, "pos2=", pos2, "max_dist=", max_dist)
        if max_dist <= 0:
            return pos1[0], pos1[1]
        x_dir = pos2[0] - pos1[1]
        y_dir = pos2[1] - pos1[1]
        print("x_dir:", x_dir, "y_dir:", y_dir)
        length = math.sqrt(x_dir ** 2 + y_dir ** 2)
        print("length:", length)
        dest_x = int(max(min((x_dir / length) * max_dist, self._og_x), 0))
        dest_y = int(max(min((y_dir / length) * max_dist, self._og_y), 0))
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

    def move(self, target, pos, real_pixels):
        print("GameController.move, target:", target, "pos:", pos, "real_pixels:", real_pixels)
        if target != self._active_char:
            return create_error("It's not your characters turn yet")
        max_dist = target.get_movement_left()
        new_pos = self._normalize_distance(target.get_pos(), pos, max_dist)
        print("new pos:", new_pos)
        dist = math.ceil(self._calc_distance(target.get_pos(), new_pos))
        target.move(new_pos, dist)
        x = self._og_x / real_pixels[0]
        y = self._og_y / real_pixels[1]
        x = round(x * new_pos[0])
        y = round(y * new_pos[1])
        return create_response()
        # return create_response({"char": target, "x": x, "y": y, "og_x": self._og_x, "og_y": self._og_y})

    def _load_character_configs(self):
        config_dir = "./configs"
        for file in os.listdir(config_dir):
            config_path = os.path.join(config_dir, file)
            if os.path.isfile(config_path) and file.endswith(".json"):
                config_name = os.path.splitext(file)[0]
                with open(config_path, "r") as reader:
                    data = json.loads(reader.read())
                    self._character_configs[config_name] = data
                    print("Loaded character config:", config_name)

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

    def get_character_configs(self, fn_filter=None):
        character_configs = self._character_configs
        if fn_filter is not None:
            character_configs = dict((k, v) for (k, v) in self._character_configs.items() if fn_filter(v))
        return character_configs

    def remove_character(self, character_id):
        dicts = [self._chars, self._pcs, self._enemies, self._allies]
        for d in dicts:
            if character_id in d:
                del d[character_id]

    def add_turn(self, name):
        c = self._chars.get(name, None)
        if c is None:
            return create_error("Character does not exist")
        self._queue.append(c)
        return create_response()

    def next_turn(self):
        if len(self._queue) == 0:
            self._round += 1
            self._queue = self._full_queue.copy()
        self._active_char.turn_over()
        name = self._active_char.get_name()
        resp = {"state": "ongoing"}
        if self._active_char.is_dead():
            self._full_queue = list(filter(lambda a: a.get_name() != self._active_char.get_name(), self._full_queue))
            self._queue = list(filter(lambda a: a.get_name() != self._active_char.get_name(), self._queue))
            if name in self._enemies.keys():
                self._dead_enemies[name] = self._active_char
                del self._enemies[name]
                del self._ko_enemies[name]
            elif name in self._enemies.keys():
                self._dead_allies[name] = self._active_char
                del self._allies[name]
                del self._ko_allies[name]
            else:
                self._dead_pcs["name"] = self._active_char
            resp["died"] = name
        if self._active_char.get_hp() == 0:
            if name in self._enemies.keys():
                self._ko_enemies[name] = self._active_char
                del self._enemies[name]
                resp["ko"] = name
            if name in self._enemies.keys():
                self._ko_allies[name] = self._active_char
                del self._allies[name]
                resp["ko"] = name
        next_char = self._queue.pop()
        self._active_char = next_char
        resp["acitve_char"] = self._active_char._id
        if len(self._enemies.keys()) == 0:
            resp["state"] = "won"
        elif len(self._allies) == 0 and len(self._dead_pcs) == len(self._pcs):
            resp["state"] = "lost"

        return resp

    def place(self, target: Character, pos, real_pixels):
        x = max(0, pos[0])
        x = min(self._og_x, x)
        y = max(0, pos[1])
        y = min(self._og_y, y)
        new_pos = [x, y]
        target.place(new_pos)

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = GameController()
        return cls._instance

    @classmethod
    def reset(cls):
        cls._instance = None
