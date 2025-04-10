import random

from combat.effects import SECS_PER_TURN
from typeclasses.scripts.scripts import Script


class AutoPass(Script):
    """Instructs an entity to pass when it is their turn in combat."""
    def at_script_creation(self):
        self.db.interval = 5
        self.key = "AutoPass"

    def at_repeat(self, **kwargs):
        if self.obj.is_turn():
            self.obj.execute_cmd("pass")


class SimpleAttack(Script):
    """Makes an entity attack a random enemy of opposite hostility to them when engaged in combat."""
    def at_script_creation(self):
        self.key = "SimpleAttack"
        self.interval = 5

    def at_repeat(self, **kwargs):
        if self.obj.is_in_combat():
            if self.obj.is_turn():
                targets = []
                for fighter in self.obj.location.scripts.get("Combat Turn Handler")[0].db.fighters:
                    if fighter.db.hostile != self.obj.db.hostile and fighter.db.hp > 0:
                        targets.append(fighter)
                target = random.choice(targets)
                self.obj.execute_cmd("attack " + target.key)
