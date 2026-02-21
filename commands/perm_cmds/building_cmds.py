from evennia.commands.cmdset import CmdSet
from evennia.commands.default.building import CmdDig, CmdTunnel
from evennia.commands.default.muxcommand import MuxCommand

from combat.combat_constants import DIRECTION_NAMES_OPPOSITES
from typeclasses.base.objects import Object


# Extended to add new room to current area unless using "delocalize" switch
class MyCmdDig(CmdDig):
    """
    build new rooms and connect them to the current location

    Usage:
      dig[/switches] <roomname>[;alias;alias...][:typeclass]
            [= <exit_to_there>[;alias][:typeclass]]
               [, <exit_to_here>[;alias][:typeclass]]

    Switches:
       tel or teleport - move yourself to the new room
       delocalize - do not assign location automatically

    Examples:
       dig kitchen = north;n, south;s
       dig house:myrooms.MyHouseTypeclass
       dig sheer cliff;cliff;sheer = climb up, climb down

    This command is a convenient way to build rooms quickly; it creates the
    new room and you can optionally set up exits back and forth between your
    current room and the new one. You can add as many aliases as you
    like to the name of the room and the exits in question; an example
    would be 'north;no;n'.
    """

    key = "@dig"
    switch_options = ("teleport", "delocalize", "keepname")
    locks = "cmd:perm(dig) or perm(Builder)"
    help_category = "Building"

    method_type = "cmd_dig"

    # lockstring of newly created rooms, for easy overloading.
    # Will be formatted with the {id} of the creating object.
    new_room_lockstring = (
        "control:id({id}) or perm(Admin); "
        "delete:id({id}) or perm(Admin); "
        "edit:id({id}) or perm(Admin)"
    )

    def func(self):
        """Do the digging. Inherits variables from ObjManipCommand.parse()"""
        old_room = self.caller.location

        caller = self.caller

        if not self.lhs:
            string = "Usage: dig[/teleport] <roomname>[;alias;alias...][:parent] [= <exit_there>"
            string += "[;alias;alias..][:parent]] "
            string += "[, <exit_back_here>[;alias;alias..][:parent]]"
            caller.msg(string)
            return

        room = self.lhs_objs[0]

        if not room["name"]:
            caller.msg("You must supply a new room name.")
            return
        location = caller.location

        # Create the new room
        room_typeclass, errors = self.get_object_typeclass(
            obj_type="room", typeclass=room["option"], method=self.method_type
        )
        if errors:
            self.msg("|rError creating room:|n %s" % errors)
        if not room_typeclass:
            return

        if "keepname" in self.switches:
            room_name = location.name
        else:
            room_name = room["name"]

        # create room
        new_room, errors = room_typeclass.create(
            room_name,
            aliases=room["aliases"],
            report_to=caller,
            caller=caller,
            method=self.method_type,
        )
        if errors:
            self.msg("|rError creating room:|n %s" % errors)
        if not new_room:
            return

        alias_string = ""
        if new_room.aliases.all():
            alias_string = " (%s)" % ", ".join(new_room.aliases.all())

        room_string = f"Created room {new_room}({new_room.dbref}){alias_string} of type {new_room.typeclass_path}."

        # create exit to room

        exit_to_string = ""
        exit_back_string = ""

        if self.rhs_objs:
            to_exit = self.rhs_objs[0]
            if not to_exit["name"]:
                exit_to_string = "\nNo exit created to new room."
            elif not location:
                exit_to_string = "\nYou cannot create an exit from a None-location."
            else:
                # Build the exit to the new room from the current one
                exit_typeclass, errors = self.get_object_typeclass(
                    obj_type="exit", typeclass=to_exit["option"], method=self.method_type
                )
                if errors:
                    self.msg("|rError creating exit:|n %s" % errors)
                if not exit_typeclass:
                    return

                new_to_exit, errors = exit_typeclass.create(
                    to_exit["name"],
                    location=location,
                    destination=new_room,
                    aliases=to_exit["aliases"],
                    report_to=caller,
                    caller=caller,
                    method=self.method_type,
                )
                if errors:
                    self.msg("|rError creating exit:|n %s" % errors)
                if not new_to_exit:
                    return

                alias_string = ""
                if new_to_exit.aliases.all():
                    alias_string = " (%s)" % ", ".join(new_to_exit.aliases.all())
                exit_to_string = (
                    f"\nCreated Exit from {location.name} to {new_room.name}:"
                    f" {new_to_exit}({new_to_exit.dbref}){alias_string}."
                )

        # Create exit back from new room

        if len(self.rhs_objs) > 1:
            # Building the exit back to the current room
            back_exit = self.rhs_objs[1]
            if not back_exit["name"]:
                exit_back_string = "\nNo back exit created."
            elif not location:
                exit_back_string = "\nYou cannot create an exit back to a None-location."
            else:
                exit_typeclass, errors = self.get_object_typeclass(
                    obj_type="exit", typeclass=back_exit["option"], method=self.method_type
                )
                if errors:
                    self.msg("|rError creating exit:|n %s" % errors)
                if not exit_typeclass:
                    return
                new_back_exit, errors = exit_typeclass.create(
                    back_exit["name"],
                    location=new_room,
                    destination=location,
                    aliases=back_exit["aliases"],
                    report_to=caller,
                    caller=caller,
                    method=self.method_type,
                )
                if errors:
                    self.msg("|rError creating exit:|n %s" % errors)
                if not new_back_exit:
                    return
                alias_string = ""
                if new_back_exit.aliases.all():
                    alias_string = " (%s)" % ", ".join(new_back_exit.aliases.all())
                exit_back_string = (
                    f"\nCreated Exit back from {new_room.name} to {location.name}:"
                    f" {new_back_exit}({new_back_exit.dbref}){alias_string}."
                )
        caller.msg(f"{room_string}{exit_to_string}{exit_back_string}")
        if new_room and "teleport" in self.switches:
            caller.move_to(new_room, move_type="teleport")

        if new_room and "delocalize" not in self.switches:
            area = old_room.db.area
            if area:
                new_room.db.area = area
                area.db.rooms.append(new_room)
                self.caller.msg(f"Area {area.name} assigned.")
            env = old_room.db.environment
            if env:
                new_room.db.environment = env
                self.caller.msg(f"{new_room.name} environment set to {env}.")


# Extended to add delocalize switch to pass to dig command
class MyCmdTunnel(CmdTunnel):
    """
      create new rooms in cardinal directions only

      Usage:
        tunnel[/switch] <direction>[:typeclass] [= <roomname>[;alias;alias;...][:typeclass]]

      Switches:
        oneway - do not create an exit back to the current location
        tel - teleport to the newly created room
        delocalize - do not assign location automatically

      Example:
        tunnel n
        tunnel n = house;mike's place;green building

      This is a simple way to build using pre-defined directions:
       |wn,ne,e,se,s,sw,w,nw|n (north, northeast etc)
       |wu,d|n (up and down)
       |wi,o|n (in and out)
      The full names (north, in, southwest, etc) will always be put as
      main name for the exit, using the abbreviation as an alias (so an
      exit will always be able to be used with both "north" as well as
      "n" for example). Opposite directions will automatically be
      created back from the new room unless the /oneway switch is given.
      For more flexibility and power in creating rooms, use dig.
      """

    key = "@tunnel"
    aliases = ["@tun"]
    switch_options = ("oneway", "tel", "delocalize", "keepname")
    locks = "cmd: perm(tunnel) or perm(Builder)"
    help_category = "Building"

    method_type = "cmd_tunnel"

    # store the direction, full name and its opposite

    def func(self):
        """Implements the tunnel command"""

        if not self.args or not self.lhs:
            string = (
                "Usage: tunnel[/switch] <direction>[:typeclass] [= <roomname>"
                "[;alias;alias;...][:typeclass]]"
            )
            self.msg(string)
            return

        # If we get a typeclass, we need to get just the exitname
        exitshort = self.lhs.split(":")[0]

        if exitshort not in DIRECTION_NAMES_OPPOSITES:
            string = "tunnel can only understand the following directions: %s." % ",".join(
                sorted(DIRECTION_NAMES_OPPOSITES.keys())
            )
            string += "\n(use dig for more freedom)"
            self.msg(string)
            return

        # retrieve all input and parse it
        exitname, backshort = DIRECTION_NAMES_OPPOSITES[exitshort]
        backname = DIRECTION_NAMES_OPPOSITES[backshort][0]

        backstring = ""
        if "oneway" not in self.switches:
            backstring = f", {backname};{backshort}"
        telswitch = ""
        if "tel" in self.switches:
            telswitch = "/teleport"

        # if we received a typeclass for the exit, add it to the alias(short name)
        if ":" in self.lhs:
            # limit to only the first : character
            exit_typeclass = ":" + self.lhs.split(":", 1)[-1]
            # exitshort and backshort are the last part of the exit strings,
            # so we add our typeclass argument after
            exitshort += exit_typeclass
            backshort += exit_typeclass

        current_room = self.caller.location
        # Get the new room's coordinates based on direction from current room
        current_room_coords = current_room.db.coordinates
        if not current_room_coords:
            self.obj.msg("Set coordinates for the current room first!")
            return
        x, y, z = current_room_coords
        match exitshort:
            case "n":
                y += 1
            case "s":
                y -= 1
            case "e":
                x += 1
            case "w":
                x -= 1
            case "nw":
                x -= 1
                y += 1
            case "ne":
                x += 1
                y += 1
            case "sw":
                x -= 1
                y -= 1
            case "se":
                x += 1
                y -= 1
            case "u":
                z += 1
            case "d":
                z -= 1
            case _:
                self.caller.msg("NOTICE: No coordinates automatically generated for new room.")

        zone = self.caller.location.zone()
        if not zone:
            self.obj.msg("Set a zone first with the locations command! Start with area > locality > zone > region")
            return
        existing_room = self.caller.location.zone().get_room(x, y, z)
        if existing_room:  # Execute @open
            openstring = f"@open {exitname};{exitshort}{backstring} = #{existing_room.dbid}"
            self.execute_cmd(openstring)
        else:  # Execute @dig
            roomname = "Some place"
            if self.rhs:
                roomname = self.rhs  # this may include aliases; that's fine.

            # build the string we will use to call dig
            delocalize = "/delocalize" if "delocalize" in self.switches else ""
            keepname = "/keepname" if "keepname" in self.switches else ""
            digstring = f"@dig{telswitch}{delocalize}{keepname} {roomname} = {exitname};{exitshort}{backstring}"
            self.execute_cmd(digstring)

            new_room = (current_room.search(exitname,
                                            candidates=[obj for obj in current_room.contents if obj.destination])
                        .destination)
            new_room.db.coordinates = (x, y, z)


class CmdDigDoor(MuxCommand):
    """
    Tunnel a new room with a door in between.

    Usage:
      digdoor <direction>[:typeclass] [= <roomname>[;alias;alias;...][:typeclass]]

    Switches:
        delocalize - do not assign location automatically

    Example:
      digdoor n
      digdoor sw = house;mike's place;green building

    Executes the "tunnel" command with the given args, converts each created exit into a door, and assigns return exits.
    """
    key = "digdoor"
    switch_options = ("delocalize", "keepname")
    locks = "cmd:perm(digdoor) or perm(Builder)"
    help_category = "building"

    def func(self):
        delocalize = "/delocalize" if "delocalize" in self.switches else ""
        keepname = "/keepname" if "keepname" in self.switches else ""
        self.execute_cmd(f"tunnel{delocalize}{keepname} " + self.args)

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
        self.execute_cmd(f"@type/update #{recent_objects[0].id} = typeclasses.inanimate.locations.exits.Door")
        self.execute_cmd(f"@type/update #{recent_objects[1].id} = typeclasses.inanimate.locations.exits.Door")

        # Set them as each other's return exit
        recent_objects[1].db.return_exit = recent_objects[0]
        recent_objects[0].db.return_exit = recent_objects[1]


class BuildingCmdSet(CmdSet):
    def at_cmdset_creation(self):
        self.add(MyCmdDig)
        self.add(MyCmdTunnel)
        self.add(CmdDigDoor())
