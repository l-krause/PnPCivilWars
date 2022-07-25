from character import Character


class PlayerCharacter(Character):

    def __init__(self, dictionary, name):
        super().__init__(dictionary)
        self._name = name

    def get_name(self):
        return self._name

    def int_roll(self):
        pass