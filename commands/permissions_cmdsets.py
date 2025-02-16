from evennia import CmdSet, Command
from evennia.commands.default.general import CmdHome


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
        from typeclasses.base.objects import Object
        recent_objects = Object.objects.order_by("-db_date_created")[:2]

        self.execute_cmd(f"@type/update #{recent_objects[0].id} = typeclasses.inanimate.exits.Door")
        self.execute_cmd(f"@type/update #{recent_objects[1].id} = typeclasses.inanimate.exits.Door")

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
