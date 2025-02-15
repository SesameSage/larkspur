from evennia import TICKER_HANDLER as tickerhandler

from turnbattle.rules import COMBAT_RULES, NONCOMBAT_TURN_TIME
from typeclasses.inanimate.items.equipment import EquipmentCharacter


class TurnBattleCharacter(EquipmentCharacter):
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

        self.db.attribs = {"Strength": 0, "Constitution": 0, "Dexterity": 0, "Perception": 0,
                           "Intelligence": 0, "Wisdom": 0, "Spirit": 0}

        self.db.max_hp = 100
        self.db.hp = self.db.max_hp
        self.db.max_stamina = 50
        self.db.stamina = self.db.max_stamina
        self.db.max_mana = 50
        self.db.mana = self.db.max_mana

        self.db.unarmed_attack = "attack"
        # TODO: Calculate instead of storing these
        self.db.unarmed_damage_range = (5, 15)
        self.db.unarmed_accuracy = 30

        self.db.effects = {}  # Set empty dict for conditions

        self.db.hostile = False

        # Subscribe character to the ticker handler
        #tickerhandler.add(NONCOMBAT_TURN_TIME, self.at_update, idstring="update")
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

    def apply_turn_conditions(self):
        """
        Applies the effect of conditions that occur at the start of each
        turn in combat, or every 30 seconds out of combat.
        """
        # Regeneration: restores 4 to 8 HP at the start of character's turn
        """if "Regeneration" in self.db.effects:
            to_heal = randint(REGEN_RATE[0], REGEN_RATE[1])  # Restore HP
            if self.db.hp + to_heal > self.db.max_hp:
                to_heal = self.db.max_hp - self.db.hp  # Cap healing to max HP
            self.db.hp += to_heal
            self.location.msg_contents("%s regains %i HP from Regeneration." % (self, to_heal))

        # Poisoned: does 4 to 8 damage at the start of character's turn
        if "Poisoned" in self.db.effects:
            to_hurt = randint(POISON_RATE[0], POISON_RATE[1])  # Deal damage
            self.rules.apply_damage(self, to_hurt)
            self.location.msg_contents("%s takes %i damage from being Poisoned." % (self, to_hurt))
            if self.db.hp <= 0:
                # Call at_defeat if poison defeats the character
                self.rules.at_defeat(self)

        # Haste: Gain an extra action in combat.
        if self.rules.is_in_combat(self) and "Haste" in self.db.effects:
            self.db.combat_actionsleft += 1
            self.msg("You gain an extra action this turn from Haste!")

        # Paralyzed: Have no actions in combat.
        if self.rules.is_in_combat(self) and "Paralyzed" in self.db.effects:
            self.db.combat_actionsleft = 0
            self.location.msg_contents("%s is Paralyzed, and can't act this turn!" % self)
            self.db.combat_turnhandler.turn_end_check(self)"""

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
        total_evasion = self.db.evasion
        self.location.more_info(f"{total_evasion} base evasion ({self.name})")

        for slot in self.db.equipment:
            equipment = self.db.equipment[slot]
            if equipment and hasattr(equipment.db, "evasion") and equipment.db.evasion:
                total_evasion += equipment.db.evasion
                self.location.more_info(f"+{equipment.db.evasion} evasion from {equipment.name} ({self.name})")

        effect = None
        if "Evasion Up" in self.db.effects:
            effect = self.db.effects["Evasion Up"]["amount"]
        if "Evasion Down" in self.db.effects:
            effect = self.db.effects["Evasion Down"]["amount"]
        if effect:
            total_evasion += effect
            self.location.more_info(f"{"+" if effect > 0 else ""}{effect} evasion from effect ({self.name})")

        self.location.more_info(f"{total_evasion} total evasion ({self.name})")
        return total_evasion
