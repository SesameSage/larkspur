from turnbattle.effects import EFFECT_SECS_PER_TURN
from typeclasses.scripts.scripts import Script


class TickCooldowns(Script):
    def at_script_creation(self):
        self.db.key = "TickCooldowns"
        self.interval = 1
        self.db.interval = 1
        self.db.incremented_this_turn = False

    def at_repeat(self, **kwargs):
        if self.obj.is_in_combat():
            if self.obj.rules.is_turn(self.obj):
                if not self.db.incremented_this_turn:
                    for ability in self.obj.db.cooldowns:
                        if self.obj.db.cooldowns[ability] > 0:
                            self.obj.db.cooldowns[ability] -= EFFECT_SECS_PER_TURN
                            if self.obj.db.cooldowns[ability] < 0:
                                self.obj.db.cooldowns[ability] = 0
                    self.db.incremented_this_turn = True
            else:
                self.db.incremented_this_turn = False
        for ability in self.obj.db.cooldowns:
            if self.obj.db.cooldowns[ability] > 0:
                self.obj.db.cooldowns[ability] -= 1

    # TODO: Tickerhandler this


class AutoPass(Script):
    def at_script_creation(self):
        self.db.interval = 5
        self.key = "AutoPass"

    def at_repeat(self, **kwargs):
        if self.obj.is_turn():
            self.obj.execute_cmd("pass")


class SimpleAttack(Script):
    def at_script_creation(self):
        self.key = "SimpleAttack"
        self.interval = 5

    def at_repeat(self, **kwargs):
        if self.obj.is_in_combat():
            if self.obj.is_turn():
                for fighter in self.obj.location.scripts.get("Combat Turn Handler")[0].db.fighters:
                    if fighter != self.obj:
                        target = fighter
                        break
                self.obj.execute_cmd("attack " + target.key)
