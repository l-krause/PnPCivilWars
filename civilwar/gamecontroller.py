import json
import logging
import math
import os.path

from utils.api import create_response, create_error
from utils.characters.character import Character
from utils.characters.npc import NPC
from utils.characters.player_character import PlayerCharacter
from utils.position import Position
from utils.vec2 import Vector2D


class GameController:

    _instance = None

    CHARACTER_ID = 1

    def __init__(self):
        self._map_size = Vector2D(1000, 683)
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
            position = Position.random([0, 0], self._map_size - [1, 1])

            if allies:
                suffix = "ally"
                target_dict = self._allies
            else:
                suffix = "enemy"
                target_dict = self._enemies

            name = f"{character_config['name']}-{len(target_dict)}_{suffix}"
            character_id = self.next_char_id()
            npc = NPC(character_id, character_config, name, position)
            target_dict[character_id] = npc
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

    def get_characters_aoe(self, start_pos, r):
        pixel_dist = r // self._og_meter
        response = []
        for c in self._chars:
            character_pos = c.get_pos()
            dist = character_pos - start_pos
            if 0 < dist[0] < 2 and 0 < dist[1] < 2:
                continue
            if dist[0] ** 2 + dist[1] ** 2 <= pixel_dist:
                response += [c]
        return response

    def get_characters_line(self, start_pos, dest_pos, r, pierce=True):
        max_dist = r // self._og_meter
        dist = start_pos.distance(dest_pos)
        if dist > max_dist:
            dest_pos = start_pos.normalize_distance(dest_pos, max_dist, self._map_size - [1, 1])
        response = []
        first_c = None
        first_dist = 0
        for c in self._chars:
            character_pos = c.get_pos()
            dist = character_pos - start_pos
            if 0 < dist[0] < 2 and 0 < dist[1] < 2:
                continue

            cross = Vector2D.cross_multiply(dist, dest_pos)
            char_dist = len(dist)
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

    def attack(self, actor: str, target: str):
        pc = self._pcs[actor]
        tar = self._chars[target]
        if not pc.has_action():
            return create_error("No Action Points available")
        weapon = self._pcs[actor].get_active_weapon()
        distance = pc.get_pos().distance(tar.get_pos(), factor=self._og_meter)
        resp = weapon.attack(distance, self._chars[target])
        if resp["success"]:
            pc.use_action()

        return resp

    def move(self, target, pos, real_pixels):
        print("GameController.move, target:", target, "pos:", pos, "real_pixels:", real_pixels)
        if target != self._active_char:
            return create_error("It's not your characters turn yet")
        max_dist = target.get_movement_left()

        new_pos = pos.normalize_distance(target.get_pos, max_dist, self._map_size - Vector2D(1, 1))
        print("new pos:", new_pos)
        dist = math.ceil(target.get_pos().distance(new_pos, factor=self._og_meter))
        target.move(new_pos, dist)
        return create_response()

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

    def place(self, target: Character, pos: Position):
        pos.to_bounds([0, 0], self._map_size - Vector2D(1, 1))
        target.place(pos)
        return create_response()

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = GameController()
        return cls._instance

    @classmethod
    def reset(cls):
        cls._instance = None
