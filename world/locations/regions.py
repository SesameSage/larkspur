from typeclasses.scripts.weather import *


class Region(Script):
    def at_script_creation(self):
        self.db.desc = ""
        self.db.minimum_rec_level = None
        self.db.zones = []
