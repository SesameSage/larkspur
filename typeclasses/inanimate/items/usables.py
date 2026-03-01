from decimal import Decimal as Dec

from evennia import EvTable
from evennia.prototypes.spawner import spawn
from evennia.utils import inherits_from
from win32pipe import PIPE_ACCEPT_REMOTE_CLIENTS

from combat.combat_constants import DamageTypes
from server import appearance
from typeclasses.inanimate.items.items import Item
from typeclasses.inanimate.items.item_funcs import ITEMFUNCS


class Usable(Item):
    """An item with an itemfunc that can be used with the use command."""

    def at_object_creation(self):
        super().at_object_creation()
        self.item_func = None
        self.db.targeted = False
        self.db.can_use_on_self = True
        self.db.self_only = False
        self.db.range = 1

    def color(self):
        return appearance.usable

    def identify(self):
        """Return a table containing details on the item such as its stats and effects."""
        table = EvTable(pretty_corners=True)
        table.add_column(f"Weight: {self.db.weight}",
                         f"Average value: {appearance.gold}{self.db.avg_value}", header=self.get_display_name())
        item_func = self.db.item_func
        func_str = ""
        match item_func:
            case "add_effect":
                for effect in self.db.kwargs["effects"]:
                    func_str = func_str + "Add " + effect["effect_key"] + " "
            case "heal":
                func_str = "Heal"
            case "cure_condition":
                for effect in self.db.kwargs["effects_cured"]:
                    func_str = func_str + "Cure " + effect + " "

        table.add_column(f"Num. Uses: {self.db.item_uses}",
                         f"Function: {func_str}",
                         header=self.color() + self.__class__.__name__)
        return table

    def check_usable(self, user, target):
        """Runs all checks on whether the item can be used in the way it was called."""
        if self.db.item_uses < 1:
            user.msg("No uses remaining!")
            return False
        if self.db.targeted and not target:
            user.msg("Must target something!")
            return False
        if target == user and not self.db.can_use_on_self:
            user.msg("You can't use that on yourself.")
            return False
        elif self.db.self_only and user != target:
            user.msg(f"{self.get_display_name(capital=True)} can only be used on yourself.")
            return False
        if target.db.combat_turnhandler and target.db.combat_turnhandler.db.grid.distance(user, target) > self.db.range:
            user.msg("Out of range for this item!")
            return False
        return True

    def use(self, user, target):
        """
        Performs the action of using an item.

        Args:
            user (obj): Character using the item
            item (obj): Item being used
            target (obj): Target of the item use
        """
        # If item can be used on self, and no target given, set target to self.
        if self.db.can_use_on_self and target is None:
            target = user

        # Ensure we can use the item the way we are trying to
        if not self.check_usable(user, target):
            return

        # Set kwargs to pass to item_func
        kwargs = {}
        if self.db.kwargs:
            kwargs = self.db.kwargs

        # Match item_func string to function
        try:
            item_func = ITEMFUNCS[self.db.item_func]
        except KeyError:  # If item_func string doesn't match to a function in ITEMFUNCS
            user.msg("ERROR: %s not defined in ITEMFUNCS" % self.db.item_func)
            return

        # Call the item function - abort if it returns False, indicating an error.
        # This performs the actual action of using the item.
        # Regardless of what the function returns (if anything), it's still executed.

        if not item_func(self, user, target, **kwargs):
            return

        # If we haven't returned yet, we assume the item was used successfully.
        # Spend one use if item has limited uses
        if self.db.item_uses:
            self.spend_item_use(user)

        # Spend an action if in combat
        if user.is_in_combat():
            user.db.combat_turnhandler.spend_action(user, 1, action_name="item")

class Consumable(Usable):
    """A usable item that is destroyed after a set number of uses."""

    def at_object_creation(self):
        super().at_object_creation()
        self.item_uses = 0

    def spend_item_use(self, user):
        """
        Spends one use on an item with limited uses.

        Args:
            item (obj): Item being used
            user (obj): Character using the item

        Notes:
            If item.db.item_consumable is 'True', the item is destroyed if it
            runs out of uses - if it's a string instead of 'True', it will also
            spawn a new object as residue, using the value of item.db.item_consumable
            as the name of the prototype to spawn.
        """
        self.db.item_uses -= 1  # Spend one use

        if self.db.item_uses > 0:  # Has uses remaining
            # Inform the player
            user.msg("%s has %i uses remaining." % (self.key.capitalize(), self.db.item_uses))

        else:  # All uses spent
            if not isinstance(self, Consumable):  # Item isn't consumable
                # Just inform the player that the uses are gone
                user.msg("%s has no uses remaining." % self.key.capitalize())

            else:  # If item is consumable
                # If the value is 'True', just destroy the item
                if isinstance(self, Consumable):
                    user.msg("%s has been consumed." % self.get_display_name(capital=True, article=True))
                    self.delete()  # Delete the spent item

                else:  # If a string, use value of item_consumable to spawn an object in its place
                    residue = spawn({"prototype": self.db.item_consumable})[0]  # Spawn the residue
                    # Move the residue to the same place as the item
                    residue.location = self.location
                    user.msg("After using %s, you are left with %s." % (self, residue))
                    self.delete()  # Delete the spent item

class Potion(Consumable):
    """A liquid consumable used on the holder for a beneficial effect."""

    def at_object_creation(self):
        super().at_object_creation()
        self.db.weight = round(Dec(1), 1)
        self.db.item_uses = 1

class Arrow(Consumable):
    """An arrow with special properties that can be 'used' while wielding a bow."""
    def at_object_creation(self):
        super().at_object_creation()
        self.db.weight = round(Dec(0.5), 1)
        self.db.item_uses = 1
        self.db.targeted = True
        self.db.can_use_on_self = False
        self.db.self_only = False
        self.db.range = 15

    def check_usable(self, user, target):
        if not super().check_usable(user, target):
            return False
        if not inherits_from(user.get_weapon(), "typeclasses.inanimate.items.equipment.weapons.Bow"):
            user.msg("Must be wielding a bow to use arrows!")
            return False
        return True
