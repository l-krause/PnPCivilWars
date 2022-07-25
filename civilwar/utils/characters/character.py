from abc import ABC, abstractmethod


class Character(ABC):

    def __init__(self, dictionary):
        self._max_life = dictionary["lifePoints"]
        self._curr_life = dictionary["lifePoints"]
        self._armor = dictionary["armorClass"]
        self._movement = dictionary["movement"]
        self._passivePerception = dictionary["passivePerception"]
        self._active_weapon = dictionary["activeWeapon"]
        self._weapons = dictionary["weapons"]

    @abstractmethod
    def get_name(self):
        pass

    @abstractmethod
    def get_armor(self):
        pass

    @abstractmethod
    def get_resistances(self):
        pass

    def get_pos(self):
        return self._pos

    def save_roll(self, attribute: str):
        pass

    def change_health(self, health):
        tmp_health = self._curr_life + health
        if tmp_health > self._max_life:
            self._curr_life = self._max_life
            return
        if tmp_health <= self._max_life * -2:
            return
        self._curr_life = tmp_health