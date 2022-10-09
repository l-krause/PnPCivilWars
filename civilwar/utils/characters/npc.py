from .character import Character
from .player_character import PlayerCharacter
from ..constants import MEELE_RANGE, OG_METER


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
        from gamecontroller import GameController
        game_controller = GameController.instance()

        if self.is_ko():
            self._death_roll()
            return
        if self.is_dead():
            return

        target_enemy = None
        enemies = self.get_enemies_with_distance(distance=self.get_movement_left() / OG_METER)
        for enemy in enemies:
            in_meele_range = list(enemy.get_enemies_with_distance(distance=MEELE_RANGE / OG_METER))
            if len(in_meele_range) <= 2:
                target_enemy = enemy
                break

        if target_enemy is not None:
            distance = self.distance(target_enemy)
            required_distance = self._active_weapon.get_max_range()
            print("Distance ", distance)
            print("Req. distance", required_distance)
            if distance > required_distance:
                self.move_towards(target_enemy, required_distance)
            game_controller.attack(self, target_enemy)
        else:

            # current weapon is ranged
            if self._active_weapon.is_ranged():

                # check if there is an enemy in range
                enemies = list(self.get_enemies_with_distance(distance=self._active_weapon.get_max_range()))
                if len(enemies) > 0:
                    game_controller.attack(self, enemies[0])
                    return

            else:

                # we have a ranged weapon, switch to it
                ranged_weapon = self.get_ranged_weapon()
                if ranged_weapon is not None:
                    self.switch_weapon(ranged_weapon)
                    return

            # move towards the nearest enemy, TODO: might be the same enemy as in first if-case
            enemy = self.get_closest_enemy()
            if enemy:
                self.move_towards(enemy, self._active_weapon.get_max_range())

    def to_json(self):
        data = super().to_json()
        data["is_ally"] = self._is_ally
        data["type"] = "npc"
        return data

    def is_allied_to(self, other):
        if self.is_ally():
            return isinstance(other, PlayerCharacter) or (isinstance(other, NPC) and other.is_ally())
        else:
            return isinstance(other, NPC) and not other.is_ally()
