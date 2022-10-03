import json
import logging
import math
import os.path

from flask_socketio import emit

from utils.api import create_response, create_error, json_serialize
from utils.characters.character import Character
from utils.characters.npc import NPC
from utils.characters.player_character import PlayerCharacter
from utils.position import Position
from utils.turn_order import GameTurnOrder
from utils.util import CaseInsensitiveDict
from utils.vec2 import Vector2D


class GameController:
    _instance = None

    CHARACTER_ID = 1

    def __init__(self):

        # map attributes
        self._map_size = Vector2D(1000, 683)
        self._og_meter = 152.5 / 434

        # game turn order + round counter + characters
        self._turn_order = GameTurnOrder()
        self._chars = {}

        # character configs
        self._character_configs = CaseInsensitiveDict()
        self._load_character_configs()

    def next_char_id(self):
        next_id = self.CHARACTER_ID
        self.CHARACTER_ID += 1
        return next_id

    def start(self):
        self._turn_order.reset()

        # list of (roll, character)-tuples
        initial_order = []
        for player_character in self.get_player_characters():
            initial_order.append((player_character.int_roll(), player_character))

        # sort the tuples by descending roll value
        initial_order = sorted(initial_order, reverse=True)

        # add all to queue
        initial_order = list(zip(*initial_order))[1]
        self._turn_order.add_all(initial_order)

        # next: add all allies
        self._turn_order.add_all(self.get_allies())

        # last: add all enemies
        self._turn_order.add_all(self.get_enemies())

        return create_response({"first": self._turn_order.get_next().get_id()})

    def create_npc(self, amount=20, allies=True):
        villager_config = self._character_configs["villager"]
        veteran_config = self._character_configs["veteran"]

        npcs = {"veterans": [], "villagers": []}

        for i in range(amount):
            character_config = (veteran_config if i % 5 == 0 else villager_config).copy()
            position = Position.random([0, 0], self._map_size - [1, 1])

            if allies:
                suffix = "ally"
            else:
                suffix = "enemy"

            name = f"{character_config['name']}-{len(self._chars)}_{suffix}"
            character_id = self.next_char_id()
            npc = NPC(character_id, character_config, name, position, allies)
            self._chars[character_id] = npc
            npc_type = "veterans" if i % 5 == 0 else "villagers"
            npcs[npc_type].append(npc)
        return create_response(npcs)

    def create_pc(self, character_name):
        logging.debug("GameController.create_pc")
        character_config = self._character_configs.get(character_name, None)
        if not character_config:
            return create_error(f"Invalid character: {character_name}")
        elif character_config["type"] != "player":
            return create_error(f"Chosen character is not a playable character")

        character_id = self.next_char_id()
        character = PlayerCharacter(character_id, character_config)
        self._chars[character_id] = character
        return character

    def get_all_characters(self):
        return self._chars

    def get_characters_by(self, f):
        return filter(f, self._chars.values())

    def get_characters_by_type(self, t):
        return filter(lambda c: isinstance(c, t), self._chars.values())

    def get_player_characters(self, only_alive=False):
        players = self.get_characters_by_type(PlayerCharacter)
        if only_alive:
            players = filter(lambda p: not p.is_dead(), players)
        return players

    def get_allies(self, only_alive=False):
        allies = self.get_characters_by(lambda c: isinstance(c, NPC) and c.is_ally())
        if only_alive:
            allies = filter(lambda a: not a.is_dead(), allies)
        return allies

    def get_enemies(self, only_alive=False):
        enemies = self.get_characters_by(lambda c: isinstance(c, NPC) and not c.is_ally())
        if only_alive:
            enemies = filter(lambda e: not e.is_dead(), enemies)
        return enemies

    def get_character(self, character_id):
        if character_id is None:
            return None
        return self._chars.get(character_id, None)

    # TODO: rewrite
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

    # TODO: rewrite
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

    def attack(self, actor: PlayerCharacter, target: Character):
        if not actor.has_action():
            return create_error("No Action Points available")
        weapon = actor.get_active_weapon()
        distance = actor.get_pos().distance(target.get_pos(), factor=self._og_meter)
        resp = weapon.attack(distance, self._chars[target])
        if resp["success"]:
            actor.use_action()

        return resp

    def move(self, target, pos):
        print("GameController.move, target:", target, "pos:", pos)
        if target != self._turn_order.get_active():
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
        if character_id in self._chars:
            del self._chars[character_id]

    def add_turn(self, character: Character):
        self._turn_order.add(character)
        return create_response()

    def next_turn(self):

        # end turn of last char
        active_char = self._turn_order.get_active()
        active_char.turn_over()

        if active_char.is_dead():
            emit("gameEvent", json_serialize({"type": "characterDied", "characterId": active_char.get_id()}))
            self._turn_order.remove(active_char)

        # start next turn
        next_char = self._turn_order.get_next()

        while self.get_game_state() == "ongoing" and isinstance(next_char, NPC):
            next_char.make_turn()
            next_char = self._turn_order.get_next()

        return create_response(data={"status": self.get_status(), "character": active_char})

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

    def get_game_state(self):
        if not any(self.get_enemies(only_alive=True)):
            return "won"
        elif not any(self.get_allies(only_alive=True)) and not any(self.get_player_characters(only_alive=True)):
            return "lost"
        else:
            return "ongoing"

    def get_status(self):
        return {
            "round": self._turn_order.get_round(),
            "active_char": self._turn_order.get_active().get_id(),
            "state": self.get_game_state()
        }
