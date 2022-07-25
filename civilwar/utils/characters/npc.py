from character import Character


class NPC(Character):

    def get_name(self):
        self._name

    def __init__(self, dictionary, name, pos):
        super().__init__(dictionary, pos)
        self._name = name
