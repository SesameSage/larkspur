from evennia import CmdSet, Command


class CmdDoor(Command):
    key = "door"
    locks = "cmd:perm(Builder)"

    def func(self):
        self.execute_cmd("tunnel " + self.args)
        from typeclasses.base.objects import Object
        recent_objects = Object.objects.order_by("-db_date_created")[:2]

        self.execute_cmd(f"@type/update #{recent_objects[0].id} = typeclasses.inanimate.exits.Door")
        self.execute_cmd(f"@type/update #{recent_objects[1].id} = typeclasses.inanimate.exits.Door")

        recent_objects[1].db.return_exit = recent_objects[0]
        recent_objects[0].db.return_exit = recent_objects[1]


class BuildingCmdSet(CmdSet):
    key = "Builder"

    def at_cmdset_creation(self):
        self.add(CmdDoor())
