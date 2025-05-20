import decimal
from decimal import Decimal

import evennia
from evennia import CmdSet
from evennia.commands.default.building import CmdDig, CmdTunnel
from evennia.commands.default.general import CmdHome
from evennia.commands.default.help import CmdSetHelp, HelpCategory, DEFAULT_HELP_CATEGORY, _loadhelp, _savehelp, \
    _quithelp
from evennia.commands.default.muxcommand import MuxCommand
from evennia.locks.lockhandler import LockException
from evennia.utils import inherits_from, create
from evennia.utils.create import create_object
from evennia.utils.eveditor import EvEditor
from evennia.utils.evtable import EvTable

from combat.abilities.all_abilities import ALL_ABILITIES
from combat.combat_constants import DIRECTION_NAMES_OPPOSITES
from server import appearance
from server.appearance import ENVIRONMENTS_BY_TYPE
from typeclasses.base.objects import Object
from typeclasses.scripts.weather import WEATHERS
from world.locations.areas import Area
from world.locations.localities import Locality
from world.locations.regions import Region
from world.locations.zones import Zone
from world.quests.quest import all_quests
from world.quests.quest_hooks import get_hook_type, print_quest_hooks


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
                        adjacent_room_localities = [obj.destination.locality() for obj in current_room.contents if
                                                    obj.destination]
                        adjacent_locality = adjacent_room_localities[0]
                        if not all(locality == adjacent_locality for locality in adjacent_room_localities):
                            self.caller.msg("Multiple adjacent localities - set locality manually.")
                            return
                        if adjacent_locality:
                            new_location.db.locality = adjacent_locality
                            adjacent_locality.db.areas.append(new_location)
                            self.caller.msg(f"Locality {adjacent_locality.name} assigned to {name}.")
                        # Start the area with the room we are in
                        current_room.db.area = new_location
                        current_room.db.area.db.rooms.append(current_room)
                        self.caller.msg(f"Current room assigned to {name} area.")
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
            if not self.lhs:
                self.caller.msg("Usage: locations/set <location>")
            location_input = self.lhs
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
    locks = "cmd:perm(env) or perm(Builder)"
    help_category = "building"

    def func(self):
        indoor_environments = ["wood room", "stone room", "cave"]
        # With no arguments, display all environment syntaxes
        if not self.lhs:
            for environment_appearance in ENVIRONMENTS_BY_TYPE:
                self.caller.msg(f"{environment_appearance}: {ENVIRONMENTS_BY_TYPE[environment_appearance]}")



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
    locks = "cmd:perm(weather) or perm(Builder)"
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
    locks = "cmd:perm(appear) or perm(Builder)"
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


class MyCmdSetHelp(CmdSetHelp):
    def func(self):
        ability_input = self.lhs
        if ability_input in ALL_ABILITIES:
            obj = create_object(typeclass=ALL_ABILITIES[ability_input], key=ability_input)
            self.rhs = obj.get_help()
            obj.delete()

        switches = self.switches
        lhslist = self.lhslist
        rhslist = self.rhslist

        if not self.args:
            self.msg(
                "Usage: sethelp[/switches] <topic>[[;alias;alias][,category[,locks]] [= <text or new category>]"
            )
            return

        nlist = len(lhslist)
        topicstr = lhslist[0] if nlist > 0 else ""
        if not topicstr:
            self.msg("You have to define a topic!")
            return
        topicstrlist = topicstr.split(";")
        topicstr, aliases = (
            topicstrlist[0],
            topicstrlist[1:] if len(topicstr) > 1 else [],
        )
        aliastxt = ("(aliases: %s)" % ", ".join(aliases)) if aliases else ""
        old_entry = None

        # check if we have an old entry with the same name

        cmd_help_topics, db_help_topics, file_help_topics = self.collect_topics(
            self.caller, mode="query"
        )
        # db-help topics takes priority over file-help
        file_db_help_topics = {**file_help_topics, **db_help_topics}
        # commands take priority over the other types
        all_topics = {**file_db_help_topics, **cmd_help_topics}
        # get all categories
        all_categories = list(
            set(HelpCategory(topic.help_category) for topic in all_topics.values())
        )
        # all available help options - will be searched in order. We also check # the
        # read-permission here.
        entries = list(all_topics.values()) + all_categories

        # default setup
        category = lhslist[1] if nlist > 1 else DEFAULT_HELP_CATEGORY
        lockstring = ",".join(lhslist[2:]) if nlist > 2 else "read:all()"

        # search for existing entries of this or other types
        old_entry = None
        for querystr in topicstrlist:
            match, _ = self.do_search(querystr, entries)
            if match:
                warning = None
                if isinstance(match, HelpCategory):
                    warning = (
                        f"'{querystr}' matches (or partially matches) the name of "
                        f"help-category '{match.key}'. If you continue, your help entry will "
                        "take precedence and the category (or part of its name) *may* not "
                        "be usable for grouping help entries anymore."
                    )
                elif inherits_from(match, "evennia.commands.command.Command"):
                    warning = (
                        f"'{querystr}' matches (or partially matches) the key/alias of "
                        f"Command '{match.key}'. Command-help take precedence over other "
                        "help entries so your help *may* be impossible to reach for those "
                        "with access to that command."
                    )
                elif inherits_from(match, "evennia.help.filehelp.FileHelpEntry"):
                    warning = (
                        f"'{querystr}' matches (or partially matches) the name/alias of the "
                        f"file-based help topic '{match.key}'. File-help entries cannot be "
                        "modified from in-game (they are files on-disk). If you continue, "
                        "your help entry may shadow the file-based one's name partly or "
                        "completely."
                    )
                if warning:
                    # show a warning for a clashing help-entry type. Even if user accepts this
                    # we don't break here since we may need to show warnings for other inputs.
                    # We don't count this as an old-entry hit because we can't edit these
                    # types of entries.
                    self.msg(f"|rWarning:\n|r{warning}|n")
                    repl = yield ("|wDo you still want to continue? Y/[N]?|n")
                    if repl.lower() in ("y", "yes"):
                        # find a db-based help entry if one already exists
                        db_topics = {**db_help_topics}
                        db_categories = list(
                            set(HelpCategory(topic.help_category) for topic in db_topics.values())
                        )
                        entries = list(db_topics.values()) + db_categories
                        match, _ = self.do_search(querystr, entries)
                        if match:
                            old_entry = match
                    else:
                        self.msg("Aborted.")
                        return
                else:
                    # a db-based help entry - this is OK
                    old_entry = match
                    category = lhslist[1] if nlist > 1 else old_entry.help_category
                    lockstring = ",".join(lhslist[2:]) if nlist > 2 else old_entry.locks.get()
                    break

        category = category.lower()

        if "edit" in switches:
            # open the line editor to edit the helptext. No = is needed.
            if old_entry:
                topicstr = old_entry.key
                if self.rhs:
                    # we assume append here.
                    old_entry.entrytext += "\n%s" % self.rhs
                helpentry = old_entry
            else:
                helpentry = create.create_help_entry(
                    topicstr,
                    self.rhs if self.rhs is not None else "",
                    category=category,
                    locks=lockstring,
                    aliases=aliases,
                )
            self.caller.db._editing_help = helpentry

            EvEditor(
                self.caller,
                loadfunc=_loadhelp,
                savefunc=_savehelp,
                quitfunc=_quithelp,
                key="topic {}".format(topicstr),
                persistent=True,
            )
            return

        if "append" in switches or "merge" in switches or "extend" in switches:
            # merge/append operations
            if not old_entry:
                self.msg(f"Could not find topic '{topicstr}'. You must give an exact name.")
                return
            if not self.rhs:
                self.msg("You must supply text to append/merge.")
                return
            if "merge" in switches:
                old_entry.entrytext += " " + self.rhs
            else:
                old_entry.entrytext += "\n%s" % self.rhs
            old_entry.aliases.add(aliases)
            self.msg(f"Entry updated:\n{old_entry.entrytext}{aliastxt}")
            return

        if "category" in switches:
            # set the category
            if not old_entry:
                self.msg(f"Could not find topic '{topicstr}'{aliastxt}.")
                return
            if not self.rhs:
                self.msg("You must supply a category.")
                return
            category = self.rhs.lower()
            old_entry.help_category = category
            self.msg(f"Category for entry '{topicstr}'{aliastxt} changed to '{category}'.")
            return

        if "locks" in switches:
            # set the locks
            if not old_entry:
                self.msg(f"Could not find topic '{topicstr}'{aliastxt}.")
                return
            show_locks = not rhslist
            clear_locks = rhslist and not rhslist[0]
            if show_locks:
                self.msg(f"Current locks for entry '{topicstr}'{aliastxt} are: {old_entry.locks}")
                return
            if clear_locks:
                old_entry.locks.clear()
                old_entry.locks.add("read:all()")
                self.msg(f"Locks for entry '{topicstr}'{aliastxt} reset to: read:all()")
                return
            lockstring = ",".join(rhslist)
            # locks.validate() does not throw an exception for things like "read:id(1),read:id(6)"
            # but locks.add() does
            existing_locks = old_entry.locks.all()
            old_entry.locks.clear()
            try:
                old_entry.locks.add(lockstring)
            except LockException as e:
                old_entry.locks.add(existing_locks)
                self.msg(str(e) + " Locks not changed.")
            else:
                self.msg(f"Locks for entry '{topicstr}'{aliastxt} changed to: {lockstring}")
            return

        if "delete" in switches or "del" in switches:
            # delete the help entry
            if not old_entry:
                self.msg(f"Could not find topic '{topicstr}'{aliastxt}.")
                return
            old_entry.delete()
            self.msg(f"Deleted help entry '{topicstr}'{aliastxt}.")
            return

        # at this point it means we want to add a new help entry.
        if not self.rhs:
            self.msg("You must supply a help text to add.")
            return
        if old_entry:
            if "replace" in switches:
                # overwrite old entry
                old_entry.key = topicstr
                old_entry.entrytext = self.rhs
                old_entry.help_category = category
                old_entry.locks.clear()
                old_entry.locks.add(lockstring)
                old_entry.aliases.add(aliases)
                old_entry.save()
                self.msg(f"Overwrote the old topic '{topicstr}'{aliastxt}.")
            else:
                self.msg(
                    f"Topic '{topicstr}'{aliastxt} already exists. Use /edit to open in editor, or "
                    "/replace, /append and /merge to modify it directly."
                )
        else:
            # no old entry. Create a new one.
            new_entry = create.create_help_entry(
                topicstr, self.rhs, category=category, locks=lockstring, aliases=aliases
            )
            if new_entry:
                self.msg(f"Topic '{topicstr}'{aliastxt} was successfully created.")
                if "edit" in switches:
                    # open the line editor to edit the helptext
                    self.caller.db._editing_help = new_entry
                    EvEditor(
                        self.caller,
                        loadfunc=_loadhelp,
                        savefunc=_savehelp,
                        quitfunc=_quithelp,
                        key="topic {}".format(new_entry.key),
                        persistent=True,
                    )
                    return
            else:
                self.msg(f"Error when creating topic '{topicstr}'{aliastxt}! Contact an admin.")


class CmdQuestEdit(MuxCommand):
    key = "questedit"
    aliases = ("qe",)
    switch_options = ("desc", "level")
    locks = "cmd:perm(questedit) or perm(Builder)"
    help_category = "building"

    def func(self):
        quests = all_quests()
        if not self.lhs:  # No args; display all quests
            table = EvTable("QID", "Level", "Description")
            for qid in quests:
                quest = quests[qid]
                level = quest.get("recommended_level", "")
                desc = quest.get("desc", "")
                table.add_row(qid, level, desc)
            self.caller.msg(table)
            return
        else:
            try:
                num_input = self.lhs.split(".")
                qid = int(num_input[0])
                stage = None
                if len(num_input) > 1:
                    stage = int(num_input[1])
            except ValueError:
                self.caller.msg(
                    f"Couldn't get integers from {self.lhs} (Usage: {appearance.cmd}questedit <qid>[.<stage>])")
                return
            if not self.rhs:
                quest = quests[qid]
                self.caller.msg(f"Quest #{qid}: {quest["desc"]}")
                table = EvTable("Stages:", "Decription", "Objective", "Object")
                stages = quest["stages"]
                for stage_num in stages:
                    stage = stages[stage_num]
                    try:
                        stage_desc = stage["desc"]
                    except KeyError:
                        stage_desc = ""
                    table.add_row(stage_num, stage_desc, stage["objective_type"], stage["object"])
                self.caller.msg(table)
                return
            else:
                try:
                    quest = evennia.GLOBAL_SCRIPTS.get("All Quests").db.quests[qid]
                except KeyError:
                    evennia.GLOBAL_SCRIPTS.get("All Quests").db.quests[qid] = \
                        {"desc": "", "recommended_level": None, "stages": {}}

                if "desc" in self.switches:
                    if stage is None:
                        try:
                            evennia.GLOBAL_SCRIPTS.get("All Quests").db.quests[qid]["desc"] = self.rhs
                        except KeyError:
                            evennia.GLOBAL_SCRIPTS.get("All Quests").db.quests[qid] = {"desc": self.rhs}
                        return
                    else:
                        try:
                            evennia.GLOBAL_SCRIPTS.get("All Quests").db.quests[qid]["stages"]
                        except KeyError:
                            evennia.GLOBAL_SCRIPTS.get("All Quests").db.quests[qid]["stages"] = {}
                        try:
                            evennia.GLOBAL_SCRIPTS.get("All Quests").db.quests[qid]["stages"][stage]["desc"] = self.rhs
                        except KeyError:
                            evennia.GLOBAL_SCRIPTS.get("All Quests").db.quests[qid]["stages"][stage] = {
                                "desc": self.rhs,
                                "objective_type":
                                    ""}
                        return
                elif "level" in self.switches:
                    try:
                        level = int(self.rhs)
                    except ValueError:
                        self.caller.msg("Couldn't get an integer level from " + self.rhs)
                    evennia.GLOBAL_SCRIPTS.get("All Quests").db.quests[qid]["recommended_level"] = level
                    return


class CmdQuestHook(MuxCommand):
    key = "questhook"
    aliases = ("qh",)
    switch_options = ("add", "remove", "edit")
    locks = "cmd:perm(questhook) or perm(Builder)"
    help_category = "building"

    def func(self):
        if not self.lhs:
            self.caller.msg(f"Must supply an object e.g. {appearance.cmd}questhook/<switch> <object> = ...")
            return
        # Arg left of "=" is object quest hook should be attached to
        obj_input = self.lhs
        obj = self.caller.search(obj_input)
        if not obj:
            return
        elif not obj.db.quest_hooks:
            self.caller.msg(f"{obj.name} doesn't handle quest hooks!")
            return

        # Creating or altering a quest hook
        rhs_needed = True
        if "remove" in self.switches or "edit" in self.switches:
            rhs_needed = False
        if self.switches:
            error_msgs = [f"Need a QID and arg! Usage: ", f"{appearance.cmd}questhook/add <object> = <qid>:<hook type>",
                          f"{appearance.cmd}questhook/msg <object> = <qid>:<stage>"]
            if not self.rhs and rhs_needed:
                for msg in error_msgs:
                    self.caller.msg(msg)
                return
            rhs_args = self.rhs.split(":")
            numbers = rhs_args[0].split(".")
            try:
                qid = int(numbers[0])
                stage = int(numbers[1])
            except ValueError:
                self.caller.msg(f"Couldn't parse {numbers[0]}.{numbers[1]} as a QID.stage integer pair")
                return
            if len(rhs_args) < 2 and rhs_needed:
                for msg in error_msgs:
                    self.caller.msg(msg)
                return

        # No switch statements: display quest hooks
        else:
            print_quest_hooks(obj, self.caller)
            return

        if "add" in self.switches:
            # Right of = is QID:hook i.e. = 3:at_give
            objective_type = rhs_args[1]
            if objective_type not in obj.db.quest_hooks:
                self.caller.msg(f"{obj.key} doesn't handle quest hooks of that type. "
                                f"Handles: {[typ for typ in obj.db.quest_hooks]}")
                return

            obj.db.quest_hooks[objective_type][qid] = {}
            obj.db.quest_hooks[objective_type][qid][stage] = {}

            quests = evennia.GLOBAL_SCRIPTS.get("All Quests").db.quests
            try:
                quests[qid]
            except KeyError:
                quests[qid] = {"stages": {}}
            try:
                quests[qid]["stages"][stage] = {}
                quests[qid]["stages"][stage]["objective_type"] = objective_type
                quests[qid]["stages"][stage]["object"] = obj
            except KeyError:
                quests[qid]["stages"][stage] = {"objective_type": objective_type, "object": obj}

        elif "remove" in self.switches:
            objective_type = get_hook_type(obj, qid, stage)
            del obj.db.quest_hooks[objective_type][qid][stage]
            del obj.db.quest_hooks[objective_type][qid]
            quests = evennia.GLOBAL_SCRIPTS.get("All Quests").db.quests
            del quests[qid]["stages"][stage]

        elif "edit" in self.switches:
            hook_type = get_hook_type(obj, qid, stage)
            options = []
            if hook_type in ["at_give", "at_defeat"] or hasattr(obj, "area") and hook_type == "at_object_receive":
                options.append("msg")
            if hook_type == "at_talk" or hasattr(obj, "hp") and hook_type == "at_object_receive":
                options.append("spoken_lines")
            if hook_type == "at_told":
                options.append("options")
            if hook_type != "at_told":
                options.append("next_stage")

            inpt = yield f"Select quest hook attribute to edit: ({str(options)})"
            match inpt:
                case "msg":
                    msg = yield "Enter message:"
                    obj.db.quest_hooks[hook_type][qid][stage]["msg"] = msg

                case "next_stage":
                    next_stage = yield "Enter next stage:"
                    obj.db.quest_hooks[hook_type][qid][stage]["next_stage"] = next_stage

                case "spoken_lines":
                    line_inpt = yield "Write lines separated by '/':"
                    lines = line_inpt.split("/")
                    lines = [line.strip() for line in lines]
                    obj.db.quest_hooks[hook_type][qid][stage]["spoken_lines"] = lines

                case "options":
                    opt_num = yield "Option number to edit:"
                    try:
                        opt_num = int(opt_num)
                    except ValueError:
                        self.caller.msg("Couldn't get an integer from " + opt_num)
                        return
                    try:
                        opt_dict = obj.db.quest_hooks[hook_type][qid][stage]["options"][opt_num]
                    except KeyError:
                        opt_dict = {"keywords": [], "spoken_lines": [], "next_stage": None}
                    attr = yield "Edit keywords, spoken_lines, or next_stage?:"
                    match attr:
                        case "keywords":
                            keywords = yield "Enter keywords separated by comma:"
                            words = keywords.split(",")
                            words = [word.strip() for word in words]
                            opt_dict["keywords"] = words
                        case "spoken_lines":
                            line_inpt = yield "Write lines separated by '/':"
                            lines = line_inpt.split("/")
                            lines = [line.strip() for line in lines]
                            opt_dict["spoken_lines"] = lines
                        case "next_stage":
                            next_stage = yield "Enter next stage:"
                            opt_dict["next_stage"] = next_stage
                        case _:
                            self.caller.msg("No valid option found for " + attr)
                            return

                    try:
                        obj.db.quest_hooks[hook_type][qid][stage]["options"][opt_num] = opt_dict
                    except KeyError:
                        obj.db.quest_hooks[hook_type][qid][stage]["options"] = []
                        obj.db.quest_hooks[hook_type][qid][stage]["options"][opt_num] = opt_dict

                case _:
                    self.caller.msg("No valid option found for " + inpt)


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
        self.add(MyCmdSetHelp)
        self.add(CmdQuestEdit)
        self.add(CmdQuestHook)
