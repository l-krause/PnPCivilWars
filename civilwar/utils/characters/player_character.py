from flask_socketio import emit

from .character import Character
import random


class PlayerCharacter(Character):

    def __init__(self, character_id, dictionary):
        super().__init__(character_id, dictionary)
        self._name = dictionary["name"]
        self._initiative = dictionary.get("initiative", 0)
        self._client_sids = set()

    def get_name(self):
        return self._name

    def int_roll(self):
        roll = random.randint(1, 20) + self._initiative
        return roll

    def to_json(self):
        data = super().to_json()
        data["type"] = "player"
        data["is_online"] = self.is_online()
        return data

    def is_allied_to(self, other):
        from .npc import NPC
        return isinstance(other, PlayerCharacter) or (isinstance(other, NPC) and other.is_ally())

    def add_client_sid(self, client_sid):
        self._client_sids.add(client_sid)

    def remove_client_sid(self, client_sid):
        if client_sid in self._client_sids:
            self._client_sids.remove(client_sid)

    def send_to(self, event, data):
        for client_sid in self._client_sids:
            emit(event, data, room=client_sid)

    def is_online(self):
        return len(self._client_sids) > 0

    def on_death_roll(self, roll):
        self.send_character_event("characterDeathRoll", {"roll": roll})
