import random

from evennia.utils import delay

from typeclasses.scripts.scripts import Script


class CombatAI(Script):
    """Dictates how an entity decides to take actions in combat."""

    def at_script_creation(self):
        super().at_script_creation()
        if not self.key:
            self.key = self.__class__.__name__

    def choose_action(self):
        entity = self.obj
        ap_left = entity.db.combat_ap
        if not ap_left:
            return

        action = "attack"
        target = self.choose_target(action)
        delay(2, self.take_action, action=action, target=target)

    def choose_target(self, action):
        # Default: choose random fighter on enemy side
        targets = []
        for fighter in self.obj.location.scripts.get("Combat Turn Handler")[0].db.fighters:
            if fighter.db.hostile_to_players != self.obj.db.hostile_to_players and fighter.db.hp > 0:
                targets.append(fighter)
        target = random.choice(targets)
        return target

    def take_action(self, action, target=None):
        if action == "attack":
            self.obj.attack(target)
        self.choose_action()