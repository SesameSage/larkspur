from decimal import Decimal as Dec

import evennia
from evennia import DefaultCharacter
from evennia import TICKER_HANDLER as tickerhandler
from evennia.utils import inherits_from
from evennia.utils.evtable import EvTable

from turnbattle.effects import DurationEffect
from typeclasses.inanimate.items.weapons import Weapon

MAX_HP_BASE = 100
LVL_TO_MAXHP = {
    1: 0,
    2: 10,
}
CON_TO_MAXHP = {
    1: 0,
    2: 10,
}
MAX_MANA_BASE = 50
LVL_TO_MAXMANA = {
    1: 0,
}
SPIRIT_TO_MAXMANA = {
    1: 0,
    2: 10,
}
MAX_STAM_BASE = 50
LVL_TO_MAXSTAM = {
    1: 0,
    2: 5,
}
STR_TO_MAXSTAM = {
    1: 0,
}

CON_TO_DEFENSE = {
    1: 0,
    2: 2,
}
DEXT_TO_EVADE = {
    1: 0,
    2: 5,
}
WIS_TO_RESIST_FACTOR = {
    1: 0,
}


class EquipmentEntity(DefaultCharacter):
    """
    Character that displays worn clothing when looked at. You can also
    just copy the return_appearance hook defined below to your own game's
    character typeclass.
    """

    def at_object_creation(self):
        super().at_object_creation()
        self.permissions.remove("player")

        self.db.char_evasion = 0
        self.db.char_defense = 0
        self.db.char_resistance = 0

        self.db.equipment = {
            "primary": None,
            "secondary": None,
            "head": None,
            "neck": None,
            "torso": None,
            "about body": None,
            "arms": None,
            # TODO: Rings
            "waist": None,
            "legs": None,
            "feet": None
        }

        self.db.unarmed_attack = "attack"
        self.db.unarmed_damage_range = (5, 15)
        self.db.unarmed_accuracy = 30

    def show_equipment(self, looker=None):
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
            carry_table.add_row(item.get_display_name(), item.get_display_desc(looker=looker))
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
        primary_held = self.db.equipment["primary"]
        if primary_held and isinstance(primary_held, Weapon):
            return primary_held


class TurnBattleEntity(EquipmentEntity):
    """
    A character able to participate in turn-based combat. Has attributes for current
    and maximum HP, and access to combat commands.
    """

    def at_object_creation(self):
        """
        Called once, when this object is first created. This is the
        normal hook to overload for most object types.
        """
        super().at_object_creation()
        # TODO: Speed?

        self.db.level = 1
        # TODO: How to utilize enemy level
        self.db.attribs = {"strength": 1, "constitution": 1,
                           "dexterity": 1, "perception": 1, "intelligence": 1,
                           "wisdom": 1, "spirit": 1}

        # TODO: When to implement calculations like max HP based on Constitution, max mana, etc
        self.db.max_hp = MAX_HP_BASE
        self.db.hp = self.db.max_hp
        self.db.hp_regen = round(Dec(0.2), 2)
        self.db.hp_buildup = Dec(0.0)

        self.db.max_stam = MAX_STAM_BASE
        self.db.stamina = self.db.max_stam
        self.db.stam_regen = round(Dec(0.2), 2)
        self.db.stam_buildup = Dec(0.0)

        self.db.max_mana = MAX_MANA_BASE
        self.db.mana = self.db.max_mana
        self.db.mana_regen = round(Dec(0.2), 2)
        self.db.mana_buildup = Dec(0.0)
        # TODO: Regen rates

        self.db.abilities = []

        self.db.mods = {}
        self.db.effects = {}

        self.db.cooldowns = {}
        # self.scripts.add(TickCooldowns)

        self.db.hostile = False

        # Subscribe character to the ticker handler
        # tickerhandler.add(NONCOMBAT_TURN_TIME, self.at_update, idstring="update")
        tickerhandler.add(1, self.at_tick, idstring="tick_effects")

        self.update_stats()

    def at_tick(self):
        if not self.is_in_combat():
            self.apply_effects()
            self.tick_cooldowns()
            if not self.is_in_combat():
                self.regenerate()

    def tick_cooldowns(self, secs=1):
        for ability in self.db.cooldowns:
            self.db.cooldowns[ability] -= secs
            if self.db.cooldowns[ability] < 0:
                self.db.cooldowns[ability] = 0

    def is_in_combat(self):
        try:
            if self.db.combat_turnhandler.is_in_combat(self):
                return True
            else:
                return False
        except AttributeError:
            return False

    def is_turn(self):
        try:
            if self.db.combat_turnhandler.is_turn(self):
                return True
            else:
                return False
        except AttributeError:
            return False

    def at_pre_move(self, destination, move_type="move", **kwargs):
        """
        Called just before starting to move this object to
        destination.

        Args:
            destination (Object): The object we are moving to

        Returns:
            shouldmove (bool): If we should move or not.

        Notes:
            If this method returns False/None, the move is cancelled
            before it is even started.

        """
        # Keep the character from moving if at 0 HP or in combat.
        if self.is_in_combat():
            self.msg("You can't exit a room while in combat!")
            return False  # Returning false keeps the character from moving.
        if self.db.HP <= 0:
            self.msg("You can't move, you've been defeated!")
            return False
        return True

    def at_turn_start(self):
        """
        Hook called at the beginning of this character's turn in combat.
        """
        # Prompt the character for their turn and give some information.
        self.msg()

        # Apply conditions that fire at the start of each turn.

    def effect_active(self, effect_key, duration_for_reset=0):
        for script in self.scripts.all():
            if script.db.effect_key == effect_key:
                return script
        return False

    def add_effect(self, typeclass, attributes=()):
        for attribute in attributes:
            if attribute[0] == "effect_key":
                effect_key = attribute[1]
            elif attribute[0] == "duration":
                duration = attribute[1]

        if self.effect_active(effect_key):
            self.effect_active(effect_key).reset_seconds(duration)
            self.location.msg_contents(f"{self.get_display_name()} regains {effect_key}.")
            return
        effect = evennia.create_script(typeclass=typeclass, obj=self, attributes=attributes)
        effect.pre_effect_add()
        self.location.msg_contents(f"{self.get_display_name()} gains {effect.color()}{effect_key}.")

    def apply_effects(self):
        for script in self.scripts.all():
            if isinstance(script, DurationEffect):
                try:
                    script.apply(in_combat=self.is_in_combat())
                except TypeError:
                    pass

    def get_attr(self, att_input: str):
        for attribute in self.db.attribs:
            if attribute.startswith(att_input):
                att_input = attribute
        base_attr = self.db.attribs[att_input]

        eq_bonus = 0
        for slot in self.db.equipment:
            equipment = self.db.equipment[slot]

        effect = 0
        if f"{att_input} Up".capitalize() in self.db.effects:
            effect = self.db.effects(f"{att_input} Up".capitalize())["amount"]
        if f"{att_input} Down".capitalize() in self.db.effects:
            effect = self.db.effects(f"{att_input} Down".capitalize())["amount"]

        return base_attr + effect + eq_bonus

    # TODO: Should other stats be in a get_ function like these, or calculated as in update_stats (faster)?
    # Defense and evasion can also depend on attacker; max hp and mana may just be changed by spells

    def get_defense(self):
        total_defense = self.db.char_defense
        self.location.more_info(f"{total_defense} base defense ({self.name})")

        for slot in self.db.equipment:
            equipment = self.db.equipment[slot]
            if equipment and hasattr(equipment.db, "defense") and equipment.db.defense:
                total_defense += equipment.db.defense
                self.location.more_info(f"+{equipment.db.defense} defense from {equipment.name} ({self.name})")

        effect = None
        if "Defense Up" in self.db.effects:
            effect = self.db.effects["Defense Up"]["amount"]
        if "Defense Down" in self.db.effects:
            effect = self.db.effects["Defense Down"]["amount"]
        if effect:
            total_defense += effect
            self.location.more_info(f"{"+" if effect > 0 else ""}{effect} defense from effect ({self.name})")

        self.location.more_info(f"{total_defense} total defense ({self.name})")
        return total_defense

    def get_evasion(self):

        def equipment_evasion():
            eq_ev = 0
            for slot in self.db.equipment:
                equipment = self.db.equipment[slot]
                if equipment and hasattr(equipment.db, "evasion") and equipment.db.evasion:
                    eq_ev += equipment.db.evasion
                    self.location.more_info(f"+{equipment.db.evasion} evasion from {equipment.name} ({self.name})")
            return eq_ev

        def effect_evasion():
            effect_ev = 0
            if "Evasion Up" in self.db.effects:
                effect_ev += self.db.effects["Evasion Up"]["amount"]
            if "Evasion Down" in self.db.effects:
                effect_ev += self.db.effects["Evasion Down"]["amount"]
            if effect_ev > 0:
                self.location.more_info(f"{"+" if effect_ev > 0 else ""}{effect_ev} evasion from effect ({self.name})")
            return effect_ev

        total_evasion = self.db.char_evasion
        self.location.more_info(f"{total_evasion} base evasion ({self.name})")
        total_evasion += equipment_evasion()
        total_evasion += effect_evasion()

        self.location.more_info(f"{total_evasion} total evasion ({self.name})")
        return total_evasion

    def get_resistance(self):
        self.location.more_info(f"{self.db.char_resistance} base resistance ({self.name})")
        eq_res = 0
        for slot in self.db.equipment:
            equipment = self.db.equipment[slot]
            if equipment and hasattr(equipment, "resistance") and equipment.db.resistance:
                eq_res += equipment.db.evasion
        effect_res = 0
        if "Resistance" in self.db.effects:
            effect_res += self.db.effects["Resistance"]["amount"]
        return self.db.char_resistance + eq_res + effect_res

    def apply_damage(self, damages):
        """
        Applies damage to a target, reducing their HP by the damage amount to a
        minimum of 0.

        Args:
            defender (obj): Character taking damage
            damages (dict): Types and amounts of damage being taken
        """
        # TODO: Effects of different damage types
        for damage_type in damages:
            self.db.hp -= damages[damage_type]  # Reduce defender's HP by the damage dealt.

        # If this reduces it to 0 or less, set HP to 0.
        if self.db.hp <= 0:
            self.db.hp = 0
            if self.is_in_combat():
                self.db.combat_turnhandler.at_defeat(defeated=self)
            else:
                self.at_defeat()

    def at_defeat(self):
        self.location.msg_contents("|w|[110%s has been defeated!" % self.name)
        for script in self.scripts.all():
            if inherits_from(script, DurationEffect):
                script.delete()
        self.update_stats()
        return True

    # TODO: Logic for who to give XP to

    def update_stats(self):
        self.db.max_hp = MAX_HP_BASE + LVL_TO_MAXHP[self.db.level] + CON_TO_MAXHP[
            self.get_attr("con")]
        self.db.max_stam = MAX_STAM_BASE + LVL_TO_MAXSTAM[self.db.level] + STR_TO_MAXSTAM[
            self.get_attr("str")]
        self.db.max_mana = MAX_MANA_BASE + LVL_TO_MAXMANA[self.db.level] + SPIRIT_TO_MAXMANA[
            self.get_attr("spi")]

        self.db.char_defense = CON_TO_DEFENSE[self.get_attr("con")]
        self.db.char_evasion = DEXT_TO_EVADE[self.get_attr("dex")]
        self.db.char_resistance = WIS_TO_RESIST_FACTOR[self.get_attr("wis")]

    def regenerate(self):
        self.db.hp_buildup += self.db.hp_regen
        self.db.mana_buildup += self.db.mana_regen
        self.db.stam_buildup += self.db.stam_regen
        if self.db.hp_buildup >= 1:
            hp_gained = int(self.db.hp_buildup)
            self.db.hp_buildup -= Dec(hp_gained)
            self.db.hp += hp_gained
        if self.db.mana_buildup >= 1:
            mana_gained = int(self.db.mana_buildup)
            self.db.mana_buildup -= Dec(mana_gained)
            self.db.mana += mana_gained
        if self.db.stam_buildup >= 1:
            stam_gained = int(self.db.stam_buildup)
            self.db.stam_buildup -= Dec(stam_gained)
            self.db.stamina += stam_gained
        self.cap_stats()

    def cap_stats(self):
        if self.db.hp > self.db.max_hp:
            self.db.hp = self.db.max_hp
        if self.db.mana > self.db.max_mana:
            self.db.mana = self.db.max_mana
        if self.db.stamina > self.db.max_stam:
            self.db.stamina = self.db.max_stam
