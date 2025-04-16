import random

from evennia.prototypes import spawner

from typeclasses.scripts.item_scripts import TemporarilyHide
from typeclasses.scripts.scripts import Script


def update_weather(region):
    weather = random.choice(region.weathers)
    for area in region.areas:
        for room in area:
            if room.db.outdoors:
                room.print_ambient(weather["desc"])


# TODO: Time of day
class ReplenishItem(Script):
    """Spawns a new item from the given item's from_prototype when the given item has been removed from its original
    location."""
    def at_script_creation(self):
        self.interval = 10
        self.db.item = None

    def at_repeat(self, **kwargs):
        if not self.db.from_prototype:
            self.db.from_prototype = self.db.item.tags.get(category="from_prototype")
        if self.db.item not in self.obj.contents:
            new_obj = spawner.spawn(self.db.from_prototype)[0]
            new_obj.move_to(self.obj, quiet=True)
            new_obj.scripts.add(TemporarilyHide())
            self.db.item = new_obj
