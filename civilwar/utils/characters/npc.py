from .character import Character


class NPC(Character):

    def get_name(self):
        return self._name

    def __init__(self, character_id, dictionary, name, pos, is_ally):
        super().__init__(character_id, dictionary, pos)
        self._name = name
        self._is_ally = is_ally

    def is_ally(self):
        return self._is_ally

    def make_turn(self):
        # TODO: NPC.make_turn()
        pass
