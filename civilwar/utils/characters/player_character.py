from .character import Character


class PlayerCharacter(Character):

    def __init__(self, character_id, dictionary):
        super().__init__(character_id, dictionary)
        self._name = dictionary["name"]
        self.is_online = True

    def get_name(self):
        return self._name

    def int_roll(self):
        pass
