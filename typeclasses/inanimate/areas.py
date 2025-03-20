from typeclasses.scripts.scripts import Script


class Area(Script):
    def at_script_creation(self):
        self.db.rooms = []  # List?


class Region(Script):
    def at_script_creation(self):
        self.db.areas = []
