from typeclasses.scripts.weather import *


class Zone(Script):
    def at_script_creation(self):
        self.db.recommended_level = None
        self.db.desc = ""

        self.db.localities = []
        self.db.region = None

        self.db.weathers = []
        self.db.current_weather = None

    def update_weather(self, weather):
        """Sets the current weather attribute on the zone, and runs update_weather on all rooms."""
        self.db.current_weather = weather
        for locality in self.db.localities:
            for area in locality.db.areas:
                for room in area.db.rooms:
                    if room.db.is_outdoors:
                        room.update_weather(weather)

    def get_room(self, x, y, z):
        coordinates = (x, y, z)
        for locality in self.db.localities:
            for area in locality.db.areas:
                for room in area.db.rooms:
                    if room.db.coordinates == coordinates:
                        return room