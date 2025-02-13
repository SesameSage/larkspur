from typeclasses.scripts.scripts import Script


class AutoPass(Script):
    def at_script_creation(self):
        self.interval = 5
        self.key = "AutoPass"

    def at_repeat(self, **kwargs):
        if hasattr(self.obj, "rules"):
            if self.obj.rules.is_turn(self.obj):
                self.obj.execute_cmd("pass")


class SimpleAttack(Script):
    def at_script_creation(self):
        self.key = "SimpleAttack"
        self.interval = 5

    def at_repeat(self, **kwargs):
        if hasattr(self.obj, "rules"):
            if self.obj.rules.is_turn(self.obj):
                for fighter in self.obj.location.scripts.get("Combat Turn Handler")[0].db.fighters:
                    if fighter != self.obj:
                        target = fighter
                        break
                self.obj.execute_cmd("attack " + target.key)
