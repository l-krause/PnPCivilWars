from utils.characters.character import Character


class GameTurnOrder:

    def __init__(self):
        self._original_queue = []
        self._round_queue = []
        self._active_char = None
        self._round = 0

    def add(self, character: Character):
        self._original_queue.append(character)

    def add_all(self, characters: [Character]):
        self._original_queue.extend(characters)

    def reset(self):
        self._original_queue = []
        self._round_queue = []
        self._round = 1
        self._active_char = None

    def get_next(self):
        if len(self._round_queue) == 0:
            if len(self._original_queue) > 0:
                self._round_queue = self._original_queue.copy()
                self._round += 1
                self._active_char = self._round_queue.pop(0)
            else:
                self._active_char = None
        else:
            self._active_char = self._round_queue.pop(0)

        return self._active_char

    def get_active(self):
        return self._active_char

    def get_round(self):
        return self._round

    def remove(self, char):
        if char in self._original_queue:
            self._original_queue.remove(char)
            if char in self._round_queue:
                self._round_queue.remove(char)
