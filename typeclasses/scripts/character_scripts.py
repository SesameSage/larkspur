import random

from combat.effects import SECS_PER_TURN
from typeclasses.scripts.scripts import Script


class CombatAI(Script):
    """Dictates how an entity decides to take actions in combat."""
    def at_script_creation(self):
        super().at_script_creation()
        if not self.key:
            self.key = self.__class__.__name__

    def take_turn(self):
        entity = self.obj

        action = self.choose_action()
        if action == "attack":
            target = self.choose_target(action)
            entity.execute_cmd("attack " + target.key)
            return

    def choose_action(self):
        return "attack"

    def choose_target(self, action):
        # Default: choose random fighter on enemy side
        targets = []
        for fighter in self.obj.location.scripts.get("Combat Turn Handler")[0].db.fighters:
            if fighter.db.hostile_to_players != self.obj.db.hostile_to_players and fighter.db.hp > 0:
                targets.append(fighter)
        target = random.choice(targets)
        return target
