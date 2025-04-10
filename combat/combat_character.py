from decimal import Decimal as Dec

import evennia
from evennia import DefaultCharacter
from evennia import TICKER_HANDLER as tickerhandler
from evennia.utils import inherits_from
from evennia.utils.evtable import EvTable

from combat.effects import DurationEffect
from typeclasses.inanimate.items.equipment.weapons import Weapon

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
    A living thing that can equip things and has defense, evasion, and resistance
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
        """Returns the primary held weapon, or None."""
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
        """Executes every second when out of combat, allowing finer control of its effects in combat."""
        if not self.is_in_combat():
            self.apply_effects()
            self.tick_cooldowns()
            if not self.is_in_combat():
                self.regenerate()

    def tick_cooldowns(self, secs=1):
        """Increments any active cooldowns down by 1 or the given number of seconds."""
        for ability in self.db.cooldowns:
            self.db.cooldowns[ability] -= secs
            if self.db.cooldowns[ability] < 0:
                self.db.cooldowns[ability] = 0

    def is_in_combat(self):
        """Returns true if this entity is currently in combat."""
        try:
            if self.db.combat_turnhandler.is_in_combat(self):
                return True
            else:
                return False
        except AttributeError:
            return False

    def is_turn(self):
        """Returns true if this entity is in combat and it is currently this entity's turn."""
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
        """If this entity currently has this effect, returns the corresponding script. If this entity does not already
        have an effect with the given key, returns False."""
        for script in self.scripts.all():
            if script.db.effect_key == effect_key:
                return script
        return False

    def add_effect(self, typeclass, attributes=None):
        """Adds or resets an effect with the given typeclass and attributes."""
        if not attributes:
            attributes = []
        if hasattr(typeclass, "fixed_attributes"):
            attributes.extend(typeclass.fixed_attributes)

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
        """Apply/increment all active effect scripts on this entity."""
        for script in self.scripts.all():
            if isinstance(script, DurationEffect):
                try:
                    script.apply(in_combat=self.is_in_combat())
                except TypeError:
                    pass

    def get_attr(self, att_input: str):
        """Gets the current effective Strength, Intelligence, etc. for this entity by attribute name."""
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
        """Returns the current effective defense for this entity, including equipment and effects."""
        self.location.more_info(f"{self.db.char_defense} base defense ({self.name})")

        eq_def = 0
        for slot in self.db.equipment:
            equipment = self.db.equipment[slot]
            if equipment and hasattr(equipment.db, "defense") and equipment.db.defense:
                eq_def += equipment.db.defense
                self.location.more_info(f"+{equipment.db.defense} defense from {equipment.name} ({self.name})")

        effect_def = 0
        if "+Defense" in self.db.effects:
            effect_def += self.db.effects["+Defense"]["amount"]
        if "-Defense" in self.db.effects:
            effect_def += self.db.effects["-Defense"]["amount"]
        if effect_def > 0:
            self.location.more_info(f"{"+" if effect_def > 0 else ""}{effect_def} defense from effects ({self.name})")

        return self.db.char_defense + eq_def + effect_def

    def get_evasion(self):
        """Returns the current effective evasion for this entity, including equipment and effects."""
        self.location.more_info(f"{self.db.char_evasion} base evasion ({self.name})")

        eq_ev = 0
        for slot in self.db.equipment:
            equipment = self.db.equipment[slot]
            if equipment and hasattr(equipment.db, "evasion") and equipment.db.evasion:
                eq_ev += equipment.db.evasion
                self.location.more_info(f"+{equipment.db.evasion} evasion from {equipment.name} ({self.name})")

        effect_ev = 0
        if "+Evasion" in self.db.effects:
            effect_ev += self.db.effects["+Evasion"]["amount"]
        if "-Evasion" in self.db.effects:
            effect_ev += self.db.effects["-Evasion"]["amount"]
        if effect_ev > 0:
            self.location.more_info(f"{"+" if effect_ev > 0 else ""}{effect_ev} evasion from effect ({self.name})")

        return self.db.char_evasion + eq_ev + effect_ev

    def get_resistance(self):
        """Returns the current effective resistance for this entity, including equipment and effects."""
        self.location.more_info(f"{self.db.char_resistance} base resistance ({self.name})")

        eq_res = 0
        for slot in self.db.equipment:
            equipment = self.db.equipment[slot]
            if equipment and hasattr(equipment, "resistance") and equipment.db.resistance:
                eq_res += equipment.db.resistance
                self.location.more_info(f"{equipment.db.resistance} resistance from {equipment.name}")

        effect_res = 0
        if "+Resistance" in self.db.effects:
            effect_res += self.db.effects["+Resistance"]["amount"]
        if "-Resistance" in self.db.effects:
            effect_res += self.db.effects["-Resistance"]["amount"]
        if effect_res > 0:
            self.location.more_info(f"{"+" if effect_res > 0 else ""}{effect_res} resistance from effect ({self.name})")

        return self.db.char_resistance + eq_res + effect_res

    def apply_damage(self, damages):
        """
        Applies damage to a target, reducing their HP by the damage amount to a
        minimum of 0.

        Args:
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
        """Called when entity is defeated."""
        self.location.msg_contents("|w|[110%s has been defeated!" % self.name)
        # End all timed buffs and debuffs
        for script in self.scripts.all():
            if inherits_from(script, DurationEffect):
                script.delete()
        self.update_stats()
        return True

    # TODO: Logic for who to give XP to

    def update_stats(self):
        """Recalculates derived stats like max hp and base evasion."""
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
        """
        Increments hp, mana, and stamina by their per-second regen values from this entity's stats.

        These regen values may be less than 1 hp/mana/stamina per second, but the target stats work in whole numbers.
        Consequently, fractional progress toward the next point gained is stored in a buildup counter on the entity.

        For example, if a player's hp_regen is 0.25, they heal 1 hp every 4 seconds. Their hp_buildup will progress
        0 > 0.25 > 0.50 > 0.75 > 1.00. On the 4th second, upon reaching 1.00, the player's hp will increase by 1, and
        the hp_buildup will lose that 1.00, carrying any overflow fraction with it (so 1.15 becomes 0.15 buildup).

        The buildup also carries fractional overflow for regen values over 1, for example handling the additional point
        added every 4 seconds for a regen value of 2.25, while still accurately incrementing the regular 2 per second.
        """
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
        """Ensure entity's hp, mana, and stamina are not greater than their maximum set values."""
        if self.db.hp > self.db.max_hp:
            self.db.hp = self.db.max_hp
        if self.db.mana > self.db.max_mana:
            self.db.mana = self.db.max_mana
        if self.db.stamina > self.db.max_stam:
            self.db.stamina = self.db.max_stam
