from typeclasses.scripts.scripts import Script


class AutoPass(Script):
    def at_script_creation(self):
        self.interval = 5

    def at_repeat(self, **kwargs):
        if hasattr(self.obj, "rules"):
            if self.obj.rules.is_turn(self.obj):
                self.obj.execute_cmd("pass")
