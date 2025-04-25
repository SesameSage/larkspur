import decimal
from decimal import Decimal

import evennia
from evennia import CmdSet
from evennia.commands.default.building import CmdDig, CmdTunnel
from evennia.commands.default.general import CmdHome
from evennia.commands.default.muxcommand import MuxCommand

from server import appearance
from typeclasses.base.objects import Object
from typeclasses.inanimate.locations.areas import Area
from typeclasses.inanimate.locations.localities import Locality
from typeclasses.inanimate.locations.regions import Region
from typeclasses.inanimate.locations.rooms import ENVIRONMENT_APPEARANCES
from typeclasses.inanimate.locations.zones import Zone
from typeclasses.scripts.weather import WEATHERS


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
    directions = {
        "n": ("north", "s"),
        "ne": ("northeast", "sw"),
        "e": ("east", "w"),
        "se": ("southeast", "nw"),
        "s": ("south", "n"),
        "sw": ("southwest", "ne"),
        "w": ("west", "e"),
        "nw": ("northwest", "se"),
        "u": ("up", "d"),
        "d": ("down", "u"),
        "i": ("in", "o"),
        "o": ("out", "i"),
    }

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

        if exitshort not in self.directions:
            string = "tunnel can only understand the following directions: %s." % ",".join(
                sorted(self.directions.keys())
            )
            string += "\n(use dig for more freedom)"
            self.msg(string)
            return

        # retrieve all input and parse it
        exitname, backshort = self.directions[exitshort]
        backname = self.directions[backshort][0]

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


class CmdLocations(MuxCommand):
    """
        add and set areas, localities, zones, or regions

        Usage:
          locations/create(/delocalize) <location type> = <location name>
          locations/set <location name>

        Switches:
            create - create a new location with the given name
            delocalize - do not assign in location hierarchy automatically
            set - assign the given location to the current room at the appropriate
                place in the hierarchy

        Examples:
           locations/create area = Kojo Monastery
           locations/set The Kojo Archipelago

        This command handles the entire hierarchy of locations (room, area, locality,
        zone, region), undertaking creation, assignment, and arrangement of location
        trees.
        """
    key = "@locations"
    switch_options = ("create", "delocalize", "set")
    locks = "cmd:perm(locations) or perm(Builder)"
    help_category = "building"

    def parse_location_type(self, input):
        location_types = [Region, Zone, Locality, Area]
        location_type = None
        for i_type in location_types:
            if i_type.__name__.lower().startswith(input.lower()):
                location_type = i_type
        if not location_type:
            self.caller.msg(f"No location type recognized for '{input}' - use region, zone, locality, or area.")
            return
        else:
            return location_type

    def func(self):
        if "create" in self.switches:
            if not self.lhs:  # left of = is location type
                self.caller.msg("Create what kind of location? locations/create <type> = <key>")
                return
            location_type = self.parse_location_type(self.lhs)
            if not location_type:
                return

            if not self.rhs:  # right of = is location name
                self.caller.msg("What to call the location? Usage: locations/create <type> = <name>")
                return
            name = self.rhs
            # TODO: validate if name already in GLOBAL_SCRIPTS.all() (when fixed)

            new_location = evennia.create_script(key=name, typeclass=location_type)
            self.caller.msg(f"New {location_type.__name__} created: {name}")

            if "delocalize" not in self.switches:
                # An area is attached to the current locality, a locality created inside the current zone, etc
                # (Always create locations from inside the super-location they should be in to make this work)
                current_room = self.caller.location
                match location_type.__name__:
                    case "Area":
                        # For areas only, an adjacent room should be used to fetch the locality. This is so areas can be
                        # easily set by creating them in a new, delocalized room
                        adjacent_rooms = [obj.destination for obj in current_room.contents if obj.destination]
                        if len(adjacent_rooms) > 1:
                            self.caller.msg("Multiple adjacent rooms - set locality manually.")
                            return
                        locality = adjacent_rooms[0].locality()
                        if locality:
                            new_location.db.locality = locality
                            locality.db.areas.append(new_location)
                            self.caller.msg(f"Locality {locality.name} assigned to {name}.")
                        # Start the area with the room we are in
                        current_room.db.area = new_location
                        current_room.db.area.db.rooms.append(current_room)
                        self.caller.msg(f"Current room assigned to {name} area.")
                    # Create localities/zones while still outside of them, before stepping into a new room to create an area
                    # (So we use current room's super)
                    case "Locality":
                        zone = current_room.zone()
                        if zone:
                            new_location.db.zone = zone
                            zone.db.localities.append(new_location)
                            self.caller.msg(f"Zone {zone.name} assigned to {name}.")
                    case "Zone":
                        region = current_room.region()
                        if region:
                            new_location.db.region = region
                            region.db.zones.append(new_location)
                            self.caller.msg(f"Region {region.name} assigned to {name}.")
                    case "Region":
                        pass

        elif "set" in self.switches:
            # Setting works in the other direction - ground-up
            current_room = self.caller.location
            location_input = self.rhs
            script = evennia.GLOBAL_SCRIPTS.get(location_input)
            if not script:
                self.caller.msg("No location script found for " + location_input)
                return

            match script.__class__.__name__:

                case "Area":
                    area = current_room.db.area
                    # Remove this room from its existing area, if it has one
                    if area:
                        try:
                            area.db.rooms.remove(current_room)
                            self.caller.msg("Current room removed from " + area.name)
                        except ValueError:
                            pass

                    # Add this room to the given area
                    current_room.db.area = script
                    script.db.rooms.append(current_room)
                    self.caller.msg("Current room's area set to " + script.name)

                case "Locality":
                    locality = current_room.locality()
                    area = current_room.db.area
                    if not area:
                        self.caller.msg("Must assign an area first.")
                        return

                    # Remove this room's area from its existing locality, if it has one
                    if locality:
                        try:
                            locality.db.areas.remove(area)
                            self.caller.msg("Current area removed from " + locality.name)
                        except ValueError:
                            pass

                    # Add current area to the given locality
                    area.db.locality = script
                    script.db.areas.append(area)
                    self.caller.msg(f"Locality for {area.name} set to " + script.name)

                case "Zone":
                    zone = current_room.zone()
                    locality = current_room.locality()
                    if not locality:
                        self.caller.msg("Must assign a locality first.")
                        return

                    # Remove this room's locality from its existing zone, if it has one
                    if zone:
                        try:
                            zone.db.localities.remove(locality)
                            self.caller.msg("Current locality removed from " + zone.name)
                        except ValueError:
                            pass

                    # Add current locality to the given zone
                    locality.db.zone = script
                    script.db.localities.append(locality)
                    self.caller.msg(f"Zone for {locality.name} set to " + script.name)

                case "Region":
                    zone = current_room.zone()
                    region = current_room.region()
                    if not zone:
                        self.caller.msg("Must assign a zone first.")
                        return
                    # Remove this room's zone from its existing region, if it has one
                    if region:
                        try:
                            region.db.zones.remove(zone)
                            self.caller.msg("Current zone removed from " + region.name)
                        except ValueError:
                            pass

                    # Add current zone to the given region
                    zone.db.region = script
                    script.db.zones.append(zone)
                    self.caller.msg(f"Region of {zone.name} set to " + script.name)


class CmdEnv(MuxCommand):
    """
        assign an environment to the current room

        Usage:
          env <environment name>

        Examples:
           env garden
           env wood room

        Environments (meadow, rainforest, cave, etc.) dictate indoor
        and outdoor effects, the appearance of the map, the spawning
        of gatherables, and more. This command handles setting and
        resetting wnvironments on the room the caller is standing in.
        """
    key = "env"
    locks = "cmd:perm(locations) or perm(Builder)"
    help_category = "building"

    def func(self):
        indoor_environments = ["wood room", "stone room", "cave"]
        # With no arguments, display all environment syntaxes
        if not self.lhs:
            for environment_appearance in ENVIRONMENT_APPEARANCES:
                self.caller.msg(f"{environment_appearance}: {ENVIRONMENT_APPEARANCES[environment_appearance]}")



        # If args given, set current room's environment to the arg
        else:
            environment = self.lhs
            room = self.caller.location
            room.db.environment = environment
            self.caller.msg(f"Set {room.name} to environment: {environment}")
            if environment in indoor_environments:
                room.db.is_outdoors = False


class CmdWeather(MuxCommand):
    """
        display and adjust weather data on the current zone

        Usage:
          weather
          weather <weather type> = <percentage of time spent>

        Examples:
           weather sunny = 75
           weather light fog = 15

        Created zones should have weather pattern data. This command
        can display, add, and change these values on the current zone.
        """
    key = "weather"
    help_category = "building"

    def func(self):
        zone = self.caller.location.zone()
        if not zone:
            self.caller.msg("No zone found here.")
            return

        # If no args given, display weathers
        if not self.lhs and not self.rhs:
            self.caller.msg("Current zone's weathers:")
            for weather_stat in zone.db.weathers:
                self.caller.msg(f"{weather_stat[0]["key"]}: {weather_stat[1] * 100}%")
            return

        if not self.lhs:
            self.caller.msg(f"What weather type? Usage: {appearance.cmd}weather <weather type> = <weight>")
            return
        weather_type_input = self.lhs

        if not self.rhs:
            self.caller.msg(
                "Assign what weight to this weather? Usage: {appearance.cmd}weather <weather type> = <weight>")
            return
        weight_input = self.rhs

        # Find weather from input
        weather_type = None
        for weather_dict in WEATHERS:
            if weather_dict["key"].lower().startswith(weather_type_input.lower()):
                weather_type = weather_dict
                break
        if not weather_type:
            self.caller.msg("No weather type found for " + weather_type_input)
            return

        # Get weight input as decimal
        try:
            weight = Decimal(weight_input)
            if weight > 1:
                weight = weight / 100
        except decimal.InvalidOperation:
            self.caller.msg(f"Couldn't interpret {weight_input} as a number")
            return

        # Remove current entry for this weather, if present
        current_weathers = zone.db.weathers
        for weather_stat in current_weathers:
            if weather_type == weather_stat[0]:
                zone.db.weathers.remove(weather_stat)

        # Add to zone's weathers
        zone.db.weathers.append((weather_type, weight))
        self.caller.msg(f"{zone.key}'s time spent in {weather_type["key"]} weather set to {weight * 100}%")

        # Check if weights total to 1.0 / 100%
        total = Decimal(0.0)
        for weather_stat in zone.db.weathers:
            total += weather_stat[1]
        if total != 1.0:
            self.caller.msg("Warning - Current weather weights do not total to 100%")


class CmdAppear(MuxCommand):
    key = "appear"
    help_category = "building"

    def func(self):
        if not self.lhs or not self.rhs:
            self.caller.msg(f"Usage: {appearance.cmd}appear <character> = <string>")
            return
        character_input = self.lhs
        string_input = self.rhs

        # Find character
        character = None
        for obj in self.caller.location.contents:
            if obj.name.lower().startswith(character_input.lower()):
                character = obj
                break
        if not character:
            self.caller.msg("No character here found for " + character_input)
            return

        character.db.appear_string = f"{character.get_display_name(article=True, capital=True)} {string_input}"
        self.caller.msg(character.db.appear_string)


class MyCmdHome(CmdHome):
    locks = "cmd:perm(Builder)"
    help_category = "navigation"


class BuildingCmdSet(CmdSet):
    key = "Builder"

    def at_cmdset_creation(self):
        self.add(MyCmdDig)
        self.add(MyCmdTunnel)
        self.add(CmdDigDoor())
        self.add(MyCmdHome)
        self.add(CmdLocations)
        self.add(CmdEnv)
        self.add(CmdWeather)
        self.add(CmdAppear)
