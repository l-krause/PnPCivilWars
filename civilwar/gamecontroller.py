import json
import logging
import os.path
import time
import copy
from threading import Lock

from flask_socketio import emit

from utils.api import create_response, create_error, json_serialize
from utils.characters.character import Character
from utils.characters.npc import NPC
from utils.characters.player_character import PlayerCharacter
from utils.position import Position
from utils.turn_order import GameTurnOrder
from utils.util import CaseInsensitiveDict
from utils.vec2 import Vector2D
from utils.constants import OG_METER


class GameController:
    _instance = None

    CHARACTER_ID = 1

    def __init__(self):

        # map attributes
        self._map_size = Vector2D(1000, 684)

        # game turn order + round counter + characters
        self._turn_order = GameTurnOrder()
        self._chars = {}
        self._changed_chars = {}
        self.mutex = Lock()

        # character configs
        self._character_configs = CaseInsensitiveDict()
        self._load_character_configs()

    @staticmethod
    def next_char_id():
        # important: do not re-use character ids!
        next_id = GameController.CHARACTER_ID
        GameController.CHARACTER_ID += 1
        return next_id

    def start(self):
        self._turn_order.reset()

        # list of (roll, character)-tuples
        initial_order = []
        for player_character in self.get_player_characters():
            initial_order.append((player_character.int_roll(), player_character))

        # sort the tuples by descending roll value
        initial_order = sorted(initial_order, reverse=True, key=lambda tuple: tuple[0])

        # add all to queue
        initial_order = list(zip(*initial_order))[1]
        self._turn_order.add_all(initial_order)

        # next: add all allies
        self._turn_order.add_all(self.get_allies())

        # last: add all enemies
        self._turn_order.add_all(self.get_enemies())

        self._turn_order.get_next()
        self.send_game_status()

    def create_npc(self, name, position, character_config, is_ally):
        character_id = self.next_char_id()
        npc = NPC(character_id, character_config, name, position, is_ally)
        self._chars[character_id] = npc
        return npc

    def create_npcs(self, amount=20, allies=True):

        if amount < 1:
            return create_error("Invalid amount, you need to create at least 1 NPC")

        villager_config = self._character_configs["villager"]
        veteran_config = self._character_configs["veteran"]
        npcs = {}

        for i in range(amount):
            character_config = (veteran_config if i % 5 == 0 else villager_config).copy()

            if allies:
                position = Position.random([0, self._map_size[1] - 150], self._map_size - [1, 1])
                suffix = "ally"
            else:
                position = Position.random([0, 0], self._map_size - [1, 150])
                suffix = "enemy"

            name = f"{character_config['name']}-{len(self._chars)}_{suffix}"
            npc = self.create_npc(name, position, character_config, allies)
            npcs[npc.get_id()] = npc

        self.send_game_event("charactersSpawned", {"characters": npcs})
        return create_response()

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

    def get_characters_by(self, *filters):
        filtered_chars = self._chars.values()
        for f in filters:
            filtered_chars = filter(f, filtered_chars)

        return filtered_chars

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

    def get_turn(self):
        return self._turn_order

    # TODO: rewrite
    def get_characters_aoe(self, start_pos, r):
        pixel_dist = r // OG_METER
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
        max_dist = r // OG_METER
        dist = start_pos.distance(dest_pos)
        if dist > max_dist:
            dest_pos = start_pos.normalize_distance(dest_pos, max_dist, self.get_map_bounds())
        response = []
        first_c = None
        first_dist = 0
        for c in self._chars:
            character_pos = c.get_pos()
            dist = character_pos - start_pos
            if 0 < dist[0] < 2 and 0 < dist[1] < 2:
                continue

            cross = Vector2D.cross_multiply(dist, dest_pos)
            char_dist = dist.length()
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
        distance = actor.get_pos().distance(target.get_pos(), factor=1/OG_METER)
        resp = weapon.attack(distance, target)

        if resp["success"]:
            actor.use_action()
            self.send_game_event("characterAttack", {"attacker": actor.get_id(), "victim": target.get_id(),
                                                   "hit": resp["data"]["hit"], "damage": resp["data"]["damage"]})

        return resp

    def move(self, target, pos):
        print("GameControlwler.move, target:", target, "pos:", pos)
        if target != self._turn_order.get_active():
            return create_error("It's not your characters turn yet")
        max_dist = target.get_movement_left() // OG_METER

        new_pos = target.get_pos().normalize_distance(pos, max_dist, self.get_map_bounds())
        print("new pos:", new_pos)
        target.move(new_pos)
        return create_response()

    def dash(self, target):
        c = self._chars[target]
        c._movement_left += c._movement
        c.use_action()
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

        self.mutex.acquire()

        # end turn of last char
        active_char = self._turn_order.get_active()

        if active_char is not None:
            if isinstance(active_char, NPC):
                is_ally = active_char.is_ally()
                next_char = active_char
                while isinstance(next_char, NPC) and is_ally == next_char.is_ally():
                    next_char.make_turn()
                    next_char.turn_over()
                    if self.get_game_state() == "ongoing":
                        next_char = self._turn_order.get_next()
                    else:
                        break
            else:
                active_char.turn_over()
                self._turn_order.get_next()

        self.mutex.release()
        self.send_game_status()
        return create_response()

    def change_char(self, target: Character, max_hp, curr_hp, armor, damage, modifier, dice):
        if target.get_id() in self._changed_chars.keys():
            self._chars[target.get_id()] = self._changed_chars.pop(target.get_id())
            data = {"curr_hp": self._chars[target.get_id()]._curr_life, "max_hp": self._chars[target.get_id()]._max_life}
            target.send_character_event("characterChangged", data)
            return
        self._changed_chars = copy.deepcopy(self._chars[target.get_id()])
        target._max_life = max_hp
        target._curr_life = curr_hp
        target._armor = armor
        weapon = target.get_active_weapon()
        weapon._dices = dice
        weapon._dice_type = damage
        weapon._additional = modifier
        data = {"curr_hp": self._chars[target.get_id()]._curr_life, "max_hp": self._chars[target.get_id()]._max_life}
        target.send_character_event("characterChangged", data)

    @staticmethod
    def send_game_event(event, data=None):
        data = {} if data is None else data
        data["type"] = event
        data["timestamp"] = int(time.time())
        emit("gameEvent", json_serialize(data), broadcast=True)
        print("Game Event:", data)

    def send_game_status(self):
        emit("gameStatus", self.get_status(), broadcast=True)

    def on_character_died(self, character: Character, reason=None):
        self._turn_order.remove(character)
        self.send_game_event("characterDied", {"characterId": character.get_id(), "reason": reason})

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
            "active_char": None if not self._turn_order.get_active() else self._turn_order.get_active().get_id(),
            "state": self.get_game_state(),
            "map": {
                "bounds": self.get_map_bounds(),
            }
        }

    def get_map_bounds(self):
        return [0, 0, self._map_size._x - 1, self._map_size._y - 1]
