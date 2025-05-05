import random

from typeclasses.scripts.scripts import Script


class CycleWeather(Script):
    def at_script_creation(self):
        self.interval = 600  # Repeat every 10 minutes
        self.db.zone = self.obj.zone()
        self.at_repeat()

    def at_repeat(self, **kwargs):
        zone = self.db.zone
        if len(zone.db.weathers) < 1:
            return
        current_weather = zone.db.current_weather
        weather_types = [weather[0] for weather in zone.db.weathers]
        weather_weights = [float(weather[1]) for weather in zone.db.weathers]
        new_weather = random.choices(population=weather_types, weights=weather_weights)[0]
        if current_weather != new_weather:
            zone.update_weather(new_weather)

SUNNY = {
    "key": "Sunny",
    "start_msg": "The clouds part, releasing the rays of the daytime sun.",
    "ongoing_msg": "The unobscured sun stands high, warming and brightening the area.",
    "effect": None,  # Reduced ignite buildup, reduced cold damage, quickens frozen effect
}
RAINING = {
    "key": "Raining",
    "start_msg": "Pitter-pattering sounds creep in as the sky darkens and begins to replenish the land with rain.",
    "ongoing_msg": "Rain is coming down at a steady pace, with mud and puddles softening the ground.",
    "effect": None,  # No burning, reduced fire damage
}
LIGHT_FOG = {
    "key": "Light fog",
    "start_msg": "Faraway things fade out of view as light fog creeps across the region.",
    "ongoing_msg": "Light fog softens the area and pales the landscape some distance away.",
    "effect": None,
}
DENSE_FOG = {
    "key": "Dense fog",
    "start_msg": "The air thickens as a dense fog rolls over the region, consuming everything more than a few paces away.",
    "ongoing_msg": "Nothing more than a few paces away can be seen through this thick fog.",
    "effect": None,  # Reduced accuracy, especially at a distance. Detecting in other rooms nearly impossible
}

WEATHERS = [SUNNY, RAINING, LIGHT_FOG, DENSE_FOG]
