from evennia import Command
from typeclasses.base.objects import Fixture

PORTAL_KEY_TO_ROOM = {
    "Napasso": "#212"
}


class Portal(Fixture):
    def at_object_creation(self):
        super().at_object_creation()
        self.db.desc = "The world appears to bend and stretch around a rift of blinding light."
        self.aliases.add("rift")


class CmdTravel(Command):
    key = "travel"
    aliases = "port", "tp", "trav"
    help_category = "navigation"

    def func(self):
        portal = self.caller.search("portal", quiet=True)
        if not portal:
            self.caller.msg("There is no portal here!")
            return
        # If args are empty, show available locations you have portal keys to
        if not self.args:
            self.caller.msg("|wAvailable locations:")
            for i, portal_key in enumerate(self.caller.db.portal_keys):
                self.caller.msg(f"{i}. {portal_key}")
        else:
            try:
                dest_name = None
                dest_name = self.caller.db.portal_keys[int(self.args)]
            except ValueError:
                for portal_key in self.caller.db.portal_keys:
                    if self.args.strip().lower() in portal_key.lower():
                        dest_name = portal_key
            if not dest_name:
                self.caller.msg("No available destination matching that name!")
            else:
                self.caller.print_ambient("You are enveloped in a cold flash of white light, and feel your innards lurch.")
                self.caller.location = PORTAL_KEY_TO_ROOM[dest_name]
                self.caller.execute_cmd("look")
