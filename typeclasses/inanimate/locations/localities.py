from typeclasses.scripts.scripts import Script


class Locality(Script):
    def at_script_creation(self):
        self.db.recommended_level = None
        self.db.desc = ""

        self.db.zone = None
        self.db.areas = []


LOCALITIES = {
    "Kojo Monastery": {
        "typeclass": "typeclasses.inanimate.locations.localities.Locality",
        "zone": "Kojo Archipelago",
        "desc": "",
        "recommended_level": 1,
    }
}

