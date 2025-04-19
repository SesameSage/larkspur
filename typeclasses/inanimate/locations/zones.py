import evennia
from evennia.utils.create import create_script

from typeclasses.scripts.weather import *


class Zone(Script):
    def at_script_creation(self):
        self.db.recommended_level = None
        self.db.desc = ""

        self.db.localities = []
        self.db.region = None

        self.db.weathers = {}
        self.db.current_weather = None

    def at_first_save(self, **kwargs):
        super().at_first_save(**kwargs)

    def update_weather(self, weather):
        for locality in self.db.localities:
            for area in locality:
                for room in area:
                    if room.db.outdoors:
                        room.update_weather(weather)


ZONES = {
    "Kojo Archipelago": {
        "typeclass": "typeclasses.inanimate.locations.zones.Zone",
        "desc": "",
        "recommended_level": 1,
    }
}

create_script(typeclass="typeclasses.inanimate.locations.zones.Zone", key="Kojo Archipelago", attributes=[("recommended_level", 1)])
