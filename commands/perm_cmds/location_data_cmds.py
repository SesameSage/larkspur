import decimal
from decimal import Decimal

import evennia
from evennia import GLOBAL_SCRIPTS
from evennia.commands.cmdset import CmdSet
from evennia.commands.default.muxcommand import MuxCommand

from server import appearance
from server.appearance import ENVIRONMENTS_BY_TYPE
from typeclasses.scripts.weather import WEATHERS
from world.locations.areas import Area
from world.locations.localities import Locality
from world.locations.regions import Region
from world.locations.zones import Zone


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
            if name in [script.key for script in GLOBAL_SCRIPTS.all()]:
                self.obj.msg("There is already a location with that name!")
                return

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
                        try:
                            adjacent_locality = adjacent_room_localities[0]
                        except IndexError:
                            adjacent_locality = None
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
        resetting environments on the room the caller is standing in.
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


class LocationCmdSet(CmdSet):
    def at_cmdset_creation(self):
        self.add(CmdLocations)
        self.add(CmdEnv)
        self.add(CmdWeather)
