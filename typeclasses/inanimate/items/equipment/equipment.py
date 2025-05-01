from evennia import default_cmds, DefaultCharacter
from evennia.commands.default.muxcommand import MuxCommand
from evennia.utils import (
    at_search_result, inherits_from,
)
from evennia.utils.evtable import EvTable

from combat.effects import DamageTypes, StatMod
from server import appearance
from typeclasses.inanimate.items.items import Item


class Equipment(Item):

    def at_object_creation(self):
        super().at_object_creation()
        self.db.desc = "An equippable item."
        self.db.equipment_slot = None

        self.db.required_level = 0
        self.db.required_stat = None
        self.db.equip_effects = {}

        self.db.equipped = False

    def identify(self):
        """Return a table containing details on the item such as its stats and effects."""
        table = EvTable()
        table.add_column(f"Weight: {self.db.weight}",
                         f"Average value: {appearance.gold}{self.db.avg_value}|n",
                         header=self.get_display_name(capital=True))
        table.add_column(f"Equip slot: {self.db.equipment_slot}",
                         f"Lvl req: {self.db.required_level}",
                         f"Requires: {self.db.required_stat}",
                         header=self.color() + self.__class__.__name__)
        defensive_stats = []
        if self.attributes.has("evasion") and self.db.evasion != 0:
            defensive_stats.append(f"Evasion: {self.db.evasion}")

        if self.attributes.has("defense"):
            for damage_type in self.db.defense:
                if self.db.defense[damage_type] != 0:
                    if damage_type is None:
                        defensive_stats.append(f"Defense: {self.db.defense[damage_type]}")
                    else:
                        defensive_stats.append(
                            f"{damage_type.get_display_name(capital=True)}: {self.db.defense[damage_type]}")

        if self.attributes.has("resistance"):
            for damage_type in self.db.resistance:
                if self.db.resistance[damage_type] != 0:
                    if damage_type is None:
                        defensive_stats.append(f"Resistance: {self.db.resistance[damage_type]}")
                    else:
                        defensive_stats.append(
                            f"{damage_type.get_display_name()} resist: {self.db.resistance[damage_type]}")

        table.table[0].add_rows(*defensive_stats)
        return table

    def color(self):
        return appearance.equipment

    def equip(self, wearer, quiet=False):
        """
        Sets equipment to equipped, and optionally echoes to the room.

        Args:
            wearer (obj): character object wearing this equipment object

        Keyword Args:
            quiet (bool): If false, does not message the room
        """
        # Replace any existing equipment
        prev_item = wearer.db.equipment[self.db.equipment_slot]
        if prev_item:
            prev_item.unequip(wearer=wearer)

        # Fill slot and set to equipped
        wearer.db.equipment[self.db.equipment_slot] = self
        self.db.equipped = True

        # Echo a message to the room
        if not quiet:
            message = f"$You() $conj(equip) {self.get_display_name(article=True)}."
            wearer.location.msg_contents(message, from_obj=wearer)

        eq_mods_mapping = {"Max HP": wearer.db.max_hp,
                           "Max Stamina": wearer.db.max_stam,
                           "Max Mana": wearer.db.max_mana,
                           "HP Regen": wearer.db.hp_regen,
                           "Stamina Regen": wearer.db.stam_regen,
                           "Mana Regen": wearer.db.mana_regen}

        if len(self.db.equip_effects) > 0:
            for effect in self.db.equip_effects:
                # Currently, all equip_effects are Stat Mods
                amount = self.db.equip_effects[effect]
                wearer.add_effect(StatMod, [("effect_key", effect), ("amount", amount), ("source", self.key)], quiet=True, stack=True)

    def unequip(self, wearer, quiet=False):
        """
        Removes worn equipment and optionally echoes to the room.

        Args:
            wearer (obj): character object wearing this equipment object

        Keyword Args:
            quiet (bool): If false, does not message the room
        """
        # Check if item is actually occupying its equipment slot
        slot = wearer.db.equipment[self.db.equipment_slot]
        if slot != self:
            wearer.msg(f"{appearance.warning}Not wearing {self.name} - cannot unequip!")
            return False

        # Remove and set to unequipped
        wearer.db.equipment[self.db.equipment_slot] = None
        self.db.equipped = False

        if self.db.equip_effects:
            for equip_effect in self.db.equip_effects:
                found = False
                for script in wearer.scripts.all():
                    if (script.attributes.has("effect_key")
                            and script.db.effect_key == equip_effect
                            and script.db.amount == self.db.equip_effects[equip_effect]):
                        script.delete()
                        found = True
                        break
                if not found:
                    wearer.msg(appearance.warning + "No script on wearer matching this equipment's equip effect")

        # Echo a message to the room
        if not quiet:
            remove_message = f"$You() $conj(unequip) {self.get_display_name(article=True)}."
            wearer.location.msg_contents(remove_message, from_obj=wearer)

        if wearer.db.equipment[self.db.equipment_slot] != self:  # If successful
            return True
        else:
            return False

    def at_drop(self, dropper, **kwargs):
        """
        Stop being wielded if dropped.
        """
        if self.db.equipped:
            self.unequip(dropper)
        if dropper.db.equipment[self.db.equipment_slot] == self:
            dropper.db.equipmnt[self.db.equipment_slot] = None
            dropper.location.msg_contents("%s unequips %s." % (dropper, self))

    def at_give(self, giver, getter, **kwargs):
        """
        Stop being worn if given.
        """
        if giver.db.equipment[self.db.equipment_slot] == self:
            giver.db.equipmnt[self.db.equipment_slot] = None
            giver.location.msg_contents("%s unequips %s." % (giver, self))


class EquipmentEntity(DefaultCharacter):
    """
    A living thing that can equip things and has defense, evasion, and resistance
    """

    def at_object_creation(self):
        super().at_object_creation()
        self.permissions.remove("player")

        self.db.char_evasion = 0
        self.db.char_defense = {None: 0, DamageTypes.BLUNT: 0, DamageTypes.SLASHING: 0, DamageTypes.PIERCING: 0}
        self.db.char_resistance = {None: 0, DamageTypes.FIRE: 0, DamageTypes.COLD: 0, DamageTypes.SHOCK: 0,
                                   DamageTypes.POISON: 0}

        # TODO: Rings
        if not self.db.equipment:
            self.db.equipment = {}
        slots = ["primary", "secondary", "head", "neck", "torso", "about body", "arms", "waist", "legs", "feet"]
        for slot in slots:
            try:
                self.db.equipment[slot]
            except (KeyError, TypeError):
                self.db.equipment[slot] = None

        self.db.unarmed_attack = "attack"
        self.db.unarmed_damage = {DamageTypes.BLUNT: (1, 5)}
        self.db.unarmed_accuracy = 30

    def show_equipment(self, looker=None):
        """Returns a table of the entity's equipment slots and what occuipes each."""
        if not looker:
            looker = self
        wear_table = EvTable(border="header")
        wear_table.add_row("\n|wEquipped:|n")
        for slot in self.db.equipment:
            if self.db.equipment[slot]:
                equipment = self.db.equipment[slot].get_display_name()
            else:
                equipment = "|=j---|n"
            wear_table.add_row(slot + ": ", equipment)
        return wear_table

    def get_display_desc(self, looker, **kwargs):
        """
        Get the 'desc' component of the object description. Called by `return_appearance`.

        Args:
            looker (Object): Object doing the looking.
            **kwargs: Arbitrary data for use when overriding.
        Returns:
            str: The desc display string.
        """
        desc = self.db.desc

        # Create outfit string
        msg = self.show_equipment(looker=looker)

        # Add on to base description
        if desc:
            desc += f"\n\n{msg}"
        else:
            desc = msg

        return desc

    def get_display_things(self, looker, **kwargs):
        """
        Get the 'things' component of the object's contents. Called by `return_appearance`.

        Args:
            looker (Object): Object doing the looking.
            **kwargs: Arbitrary data for use when overriding.
        Returns:
            str: A string describing the things in object.
        """

        def _filter_visible(obj_list):
            return (
                obj
                for obj in obj_list
                if obj != looker and obj.access(looker, "view") and not obj.db.worn
            )

        # sort and handle same-named things
        things = _filter_visible(self.contents_get(content_type="object"))

        carried = [item for item in things if not item.db.equipped]
        carry_table = EvTable(border="header")
        carry_table.add_row("\n|wCarrying:|n")
        for item in carried:
            desc = item.get_display_desc(looker=looker)
            if len(desc) > 60:
                desc = desc[:58] + "..."
            carry_table.add_row(item.get_display_name(), item.db.weight, desc)
        if carry_table.nrows <= 1:
            carry_table.add_row("Nothing.")

        return carry_table

        """grouped_things = defaultdict(list)
        for thing in things:
            grouped_things[thing.get_display_name(looker, **kwargs)].append(thing)

        thing_names = []
        for thingname, thinglist in sorted(grouped_things.items()):
            nthings = len(thinglist)
            thing = thinglist[0]
            singular, plural = thing.get_numbered_name(nthings, looker, key=thingname)
            thing_names.append(singular if nthings == 1 else plural)
        thing_names = iter_to_str(thing_names)
        return (
            f"\n{self.get_display_name(looker, **kwargs)} is carrying {thing_names}"
            if thing_names
            else ""
        )"""

    def get_weapon(self):
        """Returns the primary held weapon, or unarmed attack name."""
        primary_held = self.db.equipment["primary"]
        if primary_held and primary_held.attributes.has("damage_ranges"):
            return primary_held
        else:
            return self.db.unarmed_attack

    def ap_to_attack(self):
        weapon = self.get_weapon()
        weapon_ap = weapon.db.ap_to_attack
        if not isinstance(weapon, str) and weapon.db.ap_to_attack:
            return weapon_ap
        else:
            return 2


# <editor-fold desc="Commands">
class CmdEquip(MuxCommand):
    """
    Puts on an item of clothing you are holding.

    Usage:
      equip <obj>
      equip    (show equipped items)

    Examples:
      equip boots
      eq sword
    """

    key = "equip"
    aliases = ["equ", "eq"]
    help_category = "items"

    def func(self):
        if not self.args:
            # Show equipment
            self.caller.msg(self.caller.show_equipment())
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
                    self.caller.execute_cmd("get " + self.lhs)

        if not item_equipping:
            self.caller.msg(f"Can't find '{self.args}'")
            return
        if not item_equipping.db.equipment_slot:
            self.caller.msg(f"{item_equipping.get_display_name(capital=True)} isn't something you can equip.")
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
        if self.caller.encumbrance() + clothing.db.weight > self.caller.db.carry_weight:
            self.caller.msg("You can't carry that much!")
            return
        if self.caller.carried_count() + 1 > self.caller.db.max_carry_count:
            self.caller.msg("You can't carry that many items!")
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

        self.caller.msg(self.caller.get_display_things(looker=self.caller))
        self.caller.msg(" ")

        self.caller.msg(self.caller.table_carry_limits())


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

# </editor-fold>
