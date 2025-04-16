from evennia import CmdSet, Command
from evennia.commands.default.general import CmdHome

from typeclasses.base.objects import Object


class CmdDigDoor(Command):
    """
    Tunnel a new room with a door in between.

    Usage:
      digdoor <direction>[:typeclass] [= <roomname>[;alias;alias;...][:typeclass]]

    Example:
      digdoor n
      digdoor sw = house;mike's place;green building

    Executes the "tunnel" command with the given args, converts each created exit into a door, and assigns return exits.
    """
    key = "digdoor"
    locks = "cmd:perm(Builder)"
    help_category = "building"

    def func(self):
        self.execute_cmd("tunnel " + self.args)

        # Get the last two objects created, which should be the two new mirroring exits
        recent_objects = Object.objects.order_by("-db_date_created")[:2]

        tunnel_executed_properly = True
        if not recent_objects[0].destination or not recent_objects[1].destination:
            tunnel_executed_properly = False
        if recent_objects[1].location != self.caller.location:
            tunnel_executed_properly = False

        if not tunnel_executed_properly:
            self.caller.msg("Tunnel command did not execute properly - skipped exit type updating")
            return

        # Turn both exits into doors
        self.execute_cmd(f"@type/update #{recent_objects[0].id} = typeclasses.inanimate.exits.Door")
        self.execute_cmd(f"@type/update #{recent_objects[1].id} = typeclasses.inanimate.exits.Door")

        # Set them as each other's return exit
        recent_objects[1].db.return_exit = recent_objects[0]
        recent_objects[0].db.return_exit = recent_objects[1]


class MyCmdHome(CmdHome):
    locks = "cmd:perm(Builder)"
    help_category = "navigation"


class BuildingCmdSet(CmdSet):
    key = "Builder"

    def at_cmdset_creation(self):
        self.add(CmdDigDoor())
        self.add(MyCmdHome)
