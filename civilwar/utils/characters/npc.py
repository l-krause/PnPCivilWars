from .character import Character


class NPC(Character):

    def get_name(self):
        return self._name

    def __init__(self, character_id, dictionary, name, pos):
        super().__init__(character_id, dictionary, pos)
        self._name = name
