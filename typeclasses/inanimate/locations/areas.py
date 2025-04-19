from typeclasses.scripts.scripts import Script


class Area(Script):
    def at_script_creation(self):
        self.db.recommended_level = None
        self.db.desc = ""

        self.db.rooms = []  # List?



