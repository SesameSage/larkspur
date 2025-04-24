from decimal import Decimal as Dec

from evennia.utils.evtable import EvTable

from combat.combat_character import CombatEntity
from server import appearance
from typeclasses.base.objects import Object
from typeclasses.inanimate.items.items import Item

BASE_CARRY_WEIGHT = Dec(30)
STR_TO_CARRY_WEIGHT = {
    1: Dec(0),
    2: Dec(5),
    3: Dec(10),
    4: Dec(20),
    5: Dec(35),
    6: Dec(55),
    7: Dec(80),
}
BASE_CARRY_COUNT = 10
DEX_TO_CARRY_COUNT = {
    1: 0,
    2: 2,
    3: 3,
    4: 5,
    5: 7,
    6: 10,
}

# TODO: Command to set appear string


class LivingEntity(Object, CombatEntity):
    """
    Somthing that can move around and be killed.
    """

    def at_object_creation(self):
        super().at_object_creation()
        self.db.gold = 0
        self.appearance_template = """
{header}
|c{name}{extra_name_info}|n
{desc}
{things}
{footer}
    """
        self.db.appear_string = f"{self.get_display_name(article=True).capitalize()} is here."

        self.db.carry_weight = BASE_CARRY_WEIGHT
        self.db.max_carry_count = BASE_CARRY_COUNT

    def color(self):
        if self.db.hostile:
            return appearance.enemy
        else:
            return appearance.character

    def carried_count(self):
        carried_count = 0
        for item in self.contents:
            if isinstance(item, Item):
                if item.attributes.has("equipped") and item.db.equipped:
                    continue
                carried_count += 1
        return carried_count

    def encumbrance(self):
        encumbrance = Dec(0)
        for item in self.contents:
            if isinstance(item, Item):
                if item.attributes.has("equipped") and item.db.equipped:
                    continue
                if item.contents:
                    for content in item.contents:
                        encumbrance += content.db.weight
                encumbrance += item.db.weight

        return encumbrance

    def table_carry_limits(self):
        table = EvTable(border=None)
        table.add_row(str(self.carried_count()), "/", self.db.max_carry_count, "items")
        table.add_row(format(self.encumbrance(), ".2g"), "/", self.db.carry_weight, "weight")
        return table

    def announce_move_to(self, source_location, msg=None, mapping=None, move_type="move", **kwargs):
        """
        Called after the move if the move was not quiet. At this point
        we are standing in the new location.

        Args:
            source_location (DefaultObject): The place we came from
            msg (str, optional): the replacement message if location.
            mapping (dict, optional): additional mapping objects.
            move_type (str): The type of move. "give", "traverse", etc.
                This is an arbitrary string provided to obj.move_to().
                Useful for altering messages or altering logic depending
                on the kind of movement.
            **kwargs: Arbitrary, optional arguments for users
                overriding the call (unused by default).

        Notes:

            You can override this method and call its parent with a
            message to simply change the default message.  In the string,
            you can use the following as mappings (between braces):


            - `{object}`: the object which is moving.
            - `{exit}`: the exit from which the object is moving (if found).
            - `{origin}`: the location of the object before the move.
            - `{destination}`: the location of the object after moving.

        """

        if not self.location:
            return
        origin = source_location
        destination = self.location
        if msg:
            string = msg
        else:
            string = f"{self.get_display_name(capital=True, article=True, color=False)} "

        # Find the exit from there that leads here
        exits = [
            ex for ex in source_location.contents if ex.destination is self.location
        ]

        if len(exits) > 0:
            exit = exits[0]
            aliases = exit.aliases.all()
            from_direction = None
            cardinal_opposites = {"north": "south", "south": "north", "east": "west", "west": "east", "northeast": "southwest",
                         "northwest": "southeast", "southeast": "northwest", "southwest": "northeast"}
            if exit.name in cardinal_opposites:
                from_direction = cardinal_opposites[exit.name]
            for alias in aliases:
                if alias in cardinal_opposites:
                    from_direction = cardinal_opposites[alias]
            if from_direction:  # Came from a cardinal direction
                if not msg:
                    # "Lyrik arrives from the east."
                    string = string + f"arrives from the {from_direction}."
            else:
                if exit.name == "up" or "up" in aliases:
                    string = string + "arrives from below."
                elif exit.name == "down" or "down" in aliases:
                    string = string + "arrives from above."
                elif exit.name == "in" or "in" in aliases:
                    string = string + "comes in."
                elif "door" in exit.name or "door" in aliases:
                    string = string + "arrives through the door."
                else:
                    string = string + "arrives."
        else:
            string = string + "arrives."

        if not mapping:
            mapping = {}
        mapping.update(
            {
                "object": self,
                "exit": exits[0] if exits else "somewhere",
                "origin": origin or "nowhere",
                "destination": destination or "nowhere",
            }
        )

        destination.msg_contents(
            (appearance.ambient + string, {"type": move_type}), exclude=(self,), from_obj=self, mapping=mapping
        )

    def announce_move_from(self, destination, msg=None, mapping=None, move_type="move", **kwargs):
        """
        Called if the move is to be announced. This is
        called while we are still standing in the old
        location.

        Args:
            destination (DefaultObject): The place we are going to.
            msg (str, optional): a replacement message.
            mapping (dict, optional): additional mapping objects.
            move_type (str): The type of move. "give", "traverse", etc.
                This is an arbitrary string provided to obj.move_to().
                Useful for altering messages or altering logic depending
                on the kind of movement.
            **kwargs: Arbitrary, optional arguments for users
                overriding the call (unused by default).

        Notes:

            You can override this method and call its parent with a
            message to simply change the default message.  In the string,
            you can use the following as mappings:

            - `{object}`: the object which is moving.
            - `{exit}`: the exit from which the object is moving (if found).
            - `{origin}`: the location of the object before the move.
            - `{destination}`: the location of the object after moving.

        """
        if not self.location:
            return
        if msg:
            string = msg
        else:
            string = f"{self.get_display_name(capital=True, article=True, color=False)} "

        # Find the exit that leads there
        location = self.location
        exits = [
            ex for ex in location.contents if ex.location is location and ex.destination is destination
        ]

        if len(exits) > 0:
            exit = exits[0]
            # Is the exit in a recognized direction?
            directions = ["north", "south", "east", "west", "northeast", "northwest", "southeast", "southwest", "up",
                         "down", "in", "out"]
            # Check name
            direction = exit.name if exit.name in directions else None
            # Check aliases
            for alias in exit.aliases.all():
                if alias in directions:
                    direction = alias
            if direction:  # Exit is in a direction
                if not msg:
                    # "Lyrik goes east." "A hellhound goes out."
                    string = string + f"goes {direction}."
            else:
                string = string + "leaves."
        else:
            string = string + "leaves."

        if not mapping:
            mapping = {}
        mapping.update(
            {
                "object": self,
                "exit": exits[0] if exits else "somewhere",
                "origin": location or "nowhere",
                "destination": destination or "nowhere",
            }
        )

        location.msg_contents(
            (appearance.ambient + string, {"type": move_type}), exclude=(self,), from_obj=self, mapping=mapping
        )
