from random import randint

from evennia import DefaultCharacter
from evennia.utils import inherits_from
from evennia.utils.evtable import EvTable
from evennia import TICKER_HANDLER as tickerhandler

from server import appearance
from turnbattle.effects import DurationEffect, PerSecEffect, EffectScript
from turnbattle.rules import COMBAT_RULES
from typeclasses.living.char_stats import CharAttrib
from typeclasses.scripts.character_scripts import TickCooldowns

DEXT_TO_EVADE_FACTOR = 2


class EquipmentEntity(DefaultCharacter):
    """
    Character that displays worn clothing when looked at. You can also
    just copy the return_appearance hook defined below to your own game's
    character typeclass.
    """

    def at_object_creation(self):
        super().at_object_creation()
        self.permissions.remove("player")

        self.db.evasion = 0
        self.db.defense = 0

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


class TurnBattleEntity(EquipmentEntity):
    """
    A character able to participate in turn-based combat. Has attributes for current
    and maximum HP, and access to combat commands.
    """

    rules = COMBAT_RULES

    def at_object_creation(self):
        """
        Called once, when this object is first created. This is the
        normal hook to overload for most object types.
        """
        super().at_object_creation()

        self.db.attribs = {CharAttrib.STRENGTH: 0, CharAttrib.CONSTITUTION: 0,
                           CharAttrib.DEXTERITY: 0, CharAttrib.PERCEPTION: 0, CharAttrib.INTELLIGENCE: 0,
                           CharAttrib.WISDOM: 0, CharAttrib.SPIRIT: 0}

        self.db.max_hp = 100
        self.db.hp = self.db.max_hp
        self.db.max_stamina = 50
        self.db.stamina = self.db.max_stamina
        self.db.max_mana = 50
        self.db.mana = self.db.max_mana

        self.db.abilities = []

        self.db.unarmed_attack = "attack"
        # TODO: Calculate instead of storing these
        self.db.unarmed_damage_range = (5, 15)
        self.db.unarmed_accuracy = 30

        self.db.mods = {}
        self.db.effects = {}  # Set empty dict for conditions

        self.db.cooldowns = {}
        self.scripts.add(TickCooldowns)

        self.db.hostile = False

        # Subscribe character to the ticker handler
        # tickerhandler.add(NONCOMBAT_TURN_TIME, self.at_update, idstring="update")
        tickerhandler.add(1, self.at_tick(), idstring="tick_effects")
        """
        Adds attributes for a character's current and maximum HP.
        We're just going to set this value at '100' by default.

        An empty dictionary is created to store conditions later,
        and the character is subscribed to the Ticker Handler, which
        will call at_update() on the character, with the interval
        specified by NONCOMBAT_TURN_TIME above. This is used to tick
        down conditions out of combat.

        You may want to expand this to include various 'stats' that
        can be changed at creation and factor into combat calculations.
        """

    def at_tick(self):
        if not self.is_in_combat():
            self.apply_effects()

    def is_in_combat(self):
        if hasattr(self, "rules") and self.rules.is_in_combat(self):
            return True
        else:
            return False

    def is_turn(self):
        if hasattr(self, "rules") and self.rules.is_turn(self):
            return True
        else:
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
        if self.rules.is_in_combat(self):
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
        self.msg("|wIt's your turn! You have %i HP remaining.|n" % self.db.hp)

        # Apply conditions that fire at the start of each turn.

    def add_effect(self, effect: EffectScript):
        self.scripts.add(effect)
        self.location.msg_contents("%s gains '%s'." % (self, effect.db.effect_key))

    def apply_effects(self):
        for script in self.scripts.all():
            if inherits_from(script, DurationEffect):
                script.apply(in_combat=self.is_in_combat())

    def get_attr(self, attribute: CharAttrib):
        base_attr = self.db.attribs[attribute]

        eq_bonus = 0
        for slot in self.db.equipment:
            equipment = self.db.equipment[slot]

        effect = 0
        name = attribute.get_display_name()
        if f"{name} Up" in self.db.effects:
            effect = self.db.effects(f"{name} Up")["amount"]
        if f"{name} Down" in self.db.effects:
            effect = self.db.effects(f"{name} Down")["amount"]

        return base_attr + effect + eq_bonus

    def get_defense(self):
        total_defense = self.db.defense
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

        def base_evasion():
            dex_ev = self.get_attr(CharAttrib.DEXTERITY) * DEXT_TO_EVADE_FACTOR
            return dex_ev

        def equipment_evasion():
            eq_ev = 0
            for slot in self.db.equipment:
                equipment = self.db.equipment[slot]
                if equipment and hasattr(equipment.db, "evasion") and equipment.db.evasion:
                    eq_ev += equipment.db.evasion
                    self.location.more_info(f"+{equipment.db.evasion} evasion from {equipment.name} ({self.name})")
            return eq_ev

        def effect_evasion():
            effect = 0
            if "Evasion Up" in self.db.effects:
                effect += self.db.effects["Evasion Up"]["amount"]
            if "Evasion Down" in self.db.effects:
                effect += self.db.effects["Evasion Down"]["amount"]
            if effect > 0:
                self.location.more_info(f"{"+" if effect > 0 else ""}{effect} evasion from effect ({self.name})")
            return effect

        total_evasion = base_evasion()
        self.location.more_info(f"{total_evasion} base evasion ({self.name})")
        total_evasion += equipment_evasion()
        total_evasion += effect_evasion()

        self.location.more_info(f"{total_evasion} total evasion ({self.name})")
        return total_evasion

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
                self.rules.at_defeat(defeated=self)
            else:
                self.at_defeat()

    def at_defeat(self):
        self.location.msg_contents(f"%s{appearance.attention} has been defeated!" % self.get_display_name())
        for script in self.scripts.all():
            if inherits_from(script, DurationEffect):
                script.delete()
        return True
