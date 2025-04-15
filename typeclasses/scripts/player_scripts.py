from server import appearance
from typeclasses.scripts.scripts import Script


class LevelUpReminder(Script):
    def at_script_creation(self):
        self.key = "LevelUpReminder"
        self.interval = 120

    def at_repeat(self, **kwargs):
        self.obj.msg(appearance.notify + "Reminder: You have enough experience to level up!")
