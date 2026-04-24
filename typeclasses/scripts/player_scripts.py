from server import appearance
from typeclasses.scripts.scripts import Script


class LevelUpReminder(Script):
    def at_script_creation(self):
        self.key = "LevelUpReminder"
        self.interval = 600 # Remind every 10 minutes
        self.old_level = self.obj.db.level
        self.first_repeat = True

    def at_repeat(self, **kwargs):
        if self.first_repeat:
            self.first_repeat = False
        elif self.obj.db.level == self.old_level:
            self.obj.msg(appearance.notify + "Reminder: You have enough experience to level up!")
            self.first_repeat = False
        else:
            self.delete()
