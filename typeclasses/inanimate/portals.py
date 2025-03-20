from evennia import Command
from typeclasses.base.objects import Object


class Portal(Object):
    pass


class CmdTravel(Command):
    key = "travel"
    aliases = "port", "tp", "trav"
    help_category = "navigation"

    def func(self):
        portal = self.caller.search("portal")
        if not portal:
            self.caller.msg("There is no portal here!")
            return
        # If args are empty, show available locations you have portal keys to
