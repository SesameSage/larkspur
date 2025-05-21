from evennia import Command
from evennia.commands.cmdset import CmdSet

from typeclasses.inanimate.portals import Portal, PORTAL_KEY_TO_ROOM


class CmdTravel(Command):
    """
        jump to another portal

        Usage:
          travel <destination name>
          travel <destination number>

        Use a portal to travel to another portal, or show available destinations if none given.
        """
    key = "travel"
    aliases = "port", "tp", "trav"
    help_category = "navigation"

    def func(self):
        # Look for a portal here
        portal = self.caller.location.in_room(Portal)
        if not portal:
            self.caller.msg("There is no portal here!")
            return

        # If called without destination, show available locations you have portal keys to
        if not self.args:
            self.caller.msg("|wAvailable locations:")
            for i, portal_key in enumerate(self.caller.db.portal_keys):
                self.caller.msg(f"{i}. {portal_key}")

        else:  # Destination given
            # Look in caller's portal keys
            try:  # Try interpreting as a number
                dest_name = None
                dest_name = self.caller.db.portal_keys[int(self.args)]
            except ValueError:  # Look for a name match
                for portal_key in self.caller.db.portal_keys:
                    if self.args.strip().lower() in portal_key.lower():
                        dest_name = portal_key
            if not dest_name:
                self.caller.msg("No available destination matching that name!")
            else:
                self.caller.print_ambient(
                    "You are enveloped in a cold flash of white light, and feel your innards lurch.")
                self.caller.move_to(destination=PORTAL_KEY_TO_ROOM[dest_name], move_type="teleport")
                self.caller.execute_cmd("look")


class InteractionCmdSet(CmdSet):
    def at_cmdset_creation(self):
        self.add(CmdTravel)
