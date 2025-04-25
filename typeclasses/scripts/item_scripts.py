from typeclasses.scripts.scripts import Script


# TODO: This should probably use delay instead
class TemporarilyHide(Script):
    """Hides an item for 60 seconds."""
    def at_script_creation(self):
        self.interval = 120
        # Only triggers once, but this seems the only way to use remaining_repeats and actually wait the interval
        self.repeats = 2
        self.orig_view = self.obj.locks.get("view")
        self.orig_get = self.obj.locks.get("get")
        self.obj.locks.add("view:false();get:false()")

    def at_repeat(self, **kwargs):
        if self.remaining_repeats() == 0:
            self.obj.locks.add(f"{self.orig_view};{self.orig_get}")
            self.delete()


