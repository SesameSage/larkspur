"""
Clothing - Provides a typeclass and commands for wearable clothing,
which is appended to a character's description when worn.

Evennia contribution - Tim Ashley Jenkins 2017

Clothing items, when worn, are added to the character's description
in a list. For example, if wearing the following clothing items:

    a thin and delicate necklace
    a pair of regular ol' shoes
    one nice hat
    a very pretty dress

A character's description may look like this:

    Superuser(#1)
    This is User #1.

    Superuser is wearing one nice hat, a thin and delicate necklace,
    a very pretty dress and a pair of regular ol' shoes.

Characters can also specify the style of wear for their clothing - I.E.
to wear a scarf 'tied into a tight knot around the neck' or 'draped
loosely across the shoulders' - to add an easy avenue of customization.
For example, after entering:

    wear scarf draped loosely across the shoulders

The garment appears like so in the description:

    Superuser(#1)
    This is User #1.

    Superuser is wearing a fanciful-looking scarf draped loosely
    across the shoulders.

Items of clothing can be used to cover other items, and many options
are provided to define your own clothing types and their limits and
behaviors. For example, to have undergarments automatically covered
by outerwear, or to put a limit on the number of each type of item
that can be worn. The system as-is is fairly freeform - you
can cover any garment with almost any other, for example - but it
can easily be made more restrictive, and can even be tied into a
system for armor or other equipment.

To install, import this module and have your default character
inherit from ClothedCharacter in your game's characters.py file:

    from evennia.contrib.game_systems.clothing import ClothedCharacter

    class Character(ClothedCharacter):

And then add ClothedCharacterCmdSet in your character set in your
game's commands/default_cmdsets.py:

    from evennia.contrib.game_systems.clothing import ClothedCharacterCmdSet

    class CharacterCmdSet(default_cmds.CharacterCmdSet):
         ...
         at_cmdset_creation(self):

             super().at_cmdset_creation()
             ...
             self.add(ClothedCharacterCmdSet)    # <-- add this

From here, you can use the default builder commands to create clothes
with which to test the system:

    @create a pretty shirt : evennia.contrib.game_systems.clothing.ContribClothing
    @set shirt/clothing_type = 'top'
    wear shirt

"""

from evennia import default_cmds
from evennia.commands.default.muxcommand import MuxCommand
from evennia.utils import (
    at_search_result,
)

from server import appearance
from typeclasses.inanimate.items.items import Item


class Equipment(Item):

    def at_object_creation(self):
        super().at_object_creation()
        self.db.desc = "An equippable item."
        self.db.equipment_slot = None
        self.db.equipped = False
        self.db.required_level = 0
        self.db.equip_effect = None

    def equip(self, wearer, quiet=False):
        """
        Sets clothes to 'worn' and optionally echoes to the room.

        Args:
            wearer (obj): character object wearing this clothing object

        Keyword Args:
            quiet (bool): If false, does not message the room
        """
        # Replace any existing equipment
        prev_item = wearer.db.equipment[self.db.equipment_slot]
        if prev_item:
            prev_item.unequip(wearer=wearer, quiet=True)

        # Set clothing as worn
        wearer.db.equipment[self.db.equipment_slot] = self
        self.db.equipped = True

        # Echo a message to the room
        if not quiet:
            message = f"$You() $conj(equip) {self.name}."
            wearer.location.msg_contents(message, from_obj=wearer)

    def unequip(self, wearer, quiet=False):
        """
        Removes worn clothes and optionally echoes to the room.

        Args:
            wearer (obj): character object wearing this clothing object

        Keyword Args:
            quiet (bool): If false, does not message the room
        """
        slot = wearer.db.equipment[self.db.equipment_slot]
        if slot != self:
            wearer.msg(f"{appearance.warning}Not wearing {self.name} - cannot unequip!")
            return False

        wearer.db.equipment[self.db.equipment_slot] = None
        self.db.equipped = False

        # Echo a message to the room
        if not quiet:
            remove_message = f"$You() $conj(unequip) {self.get_display_name()}."
            wearer.location.msg_contents(remove_message, from_obj=wearer)

        if wearer.db.equipment[self.db.equipment_slot] == self:
            return True
        else:
            return False


# COMMANDS START HERE


class CmdEquip(MuxCommand):
    """
    Puts on an item of clothing you are holding.

    Usage:
      equip <obj> [=] [wear style]

    Examples:
      equip boots
      eq sword
    """

    key = "equip"
    aliases = ["equ", "eq"]
    help_category = "items"

    def func(self):
        if not self.args:
            self.caller.msg("Usage: equip <obj>")
            return
        if not self.rhs:
            # check if the whole string is an object
            item_equipping = self.caller.search(self.lhs, candidates=self.caller.contents, quiet=True)
            if not item_equipping:
                item_equipping = self.caller.search(self.lhs, candidates=self.caller.location.contents, quiet=True)
                if item_equipping:
                    self.caller.execute_cmd("get " + self.lhs)
                    item_equipping = at_search_result(item_equipping, self.caller, self.lhs)
                else:
                    self.caller.msg(f"Can't find '{self.args}'")
                    return
            else:
                # pass the result through the search-result hook
                item_equipping = at_search_result(item_equipping, self.caller, self.lhs)

        else:
            # it had an explicit separator - just do a normal search for the lhs
            item_equipping = self.caller.search(self.lhs, candidates=self.caller.contents)
            if not item_equipping:
                item_equipping = self.caller.search(self.lhs, candidates=self.caller.location.contents, quiet=True)
                if item_equipping:
                    self.caller.excute_cmd("get " + self.lhs)

        if not item_equipping:
            self.caller.msg(f"Can't find '{self.args}'")
            return
        if not item_equipping.db.equipment_slot:
            self.caller.msg(f"{item_equipping.get_display_name().capitalize()} isn't something you can wear.")
            return

        if self.caller.db.equipment[item_equipping.db.equipment_slot] == item_equipping:
            self.caller.msg(f"You're already wearing your {item_equipping.get_display_name()}.")
            return

        if self.caller.db.level < item_equipping.db.required_level:
            self.caller.msg(f"{item_equipping.get_display_name().capitalize()} requires character level "
                            f"{item_equipping.db.required_level} ({self.caller.name} is level {self.caller.db.level})")
            return

        item_equipping.equip(self.caller)


class CmdUnequip(MuxCommand):
    """
    Takes off an item of clothing.

    Usage:
       remove <obj>

    Removes an item of clothing you are wearing. You can't remove
    clothes that are covered up by something else - you must take
    off the covering item first.
    """

    key = "unequip"
    aliases = ["rem", "remove", "unequ", "uneq"]
    help_category = "items"

    def func(self):
        if not self.args:
            self.caller.msg("Usage: unequip <worn clothing object>")
            return
        clothing = self.caller.search(self.args, candidates=self.caller.db.equipment.values())
        if not clothing:
            self.caller.msg("You don't have anything like that.")
            return
        if not self.caller.db.equipment[clothing.db.equipment_slot] == clothing:
            self.caller.msg(f"You're not wearing {clothing.get_display_name()}!")
            return
        clothing.unequip(self.caller)


class CmdInventory(MuxCommand):
    """
    view inventory

    Usage:
      inventory
      inv

    Shows your inventory.
    """

    # Alternate version of the inventory command which separates
    # worn and carried items.

    key = "inventory"
    aliases = ["inv", "i"]
    locks = "cmd:all()"
    arg_regex = r"$"
    help_category = "items"

    def func(self):
        """check inventory"""
        if not self.caller.contents:
            self.caller.msg("You are not carrying or wearing anything.")
            return

        # carried items
        self.caller.msg(self.caller.get_display_things(looker=self.caller))

        # worn items
        self.caller.msg(self.caller.show_equipment())


class EquipmentCharacterCmdSet(default_cmds.CharacterCmdSet):
    """
    Command set for clothing, including new versions of 'give' and 'drop'
    that take worn and covered clothing into account, as well as a new
    version of 'inventory' that differentiates between carried and worn
    items.
    """

    key = "DefaultCharacter"

    def at_cmdset_creation(self):
        """
        Populates the cmdset
        """
        super().at_cmdset_creation()
        #
        # any commands you add below will overload the default ones.
        #
        self.add(CmdEquip())
        self.add(CmdUnequip())
        self.add(CmdInventory())