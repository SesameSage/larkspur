from evennia.prototypes import spawner

from typeclasses.scripts.scripts import Script


class TemporarilyHide(Script):
    """Hides an item for 60 seconds."""
    def at_script_creation(self):
        self.interval = 60
        # Only triggers once, but this seems the only way to use remaining_repeats and actually wait the interval
        self.repeats = 2
        self.orig_view = self.obj.locks.get("view")
        self.orig_get = self.obj.locks.get("get")
        self.obj.locks.add("view:false();get:false()")

    def at_repeat(self, **kwargs):
        if self.remaining_repeats() == 0:
            self.obj.locks.add(f"{self.orig_view};{self.orig_get}")
            self.delete()


class ReplenishItem(Script):
    """Spawns a new item from the given item's from_prototype when the given item has been removed from its original
    location."""
    # TODO: This breaks if the object is destroyed or cleared of scripts before the interval
    def at_script_creation(self):
        self.interval = 10
        self.location = self.obj.location

    def at_repeat(self, **kwargs):
        if self.obj not in self.location.contents:
            prototype = self.obj.tags.get(category="from_prototype")
            new_obj = spawner.spawn(prototype)[0]
            new_obj.scripts.add(TemporarilyHide())
            new_obj.scripts.add(ReplenishItem())
            self.delete()
