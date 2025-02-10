"""
Simple turn-based combat system

Contrib - Tim Ashley Jenkins 2017, Refactor by Griatch 2022

This is a framework for a simple turn-based combat system, similar
to those used in D&D-style tabletop role playing games. It allows
any character to start a fight in a room, at which point initiative
is rolled and a turn order is established. Each participant in combat
has a limited time to decide their action for that turn (30 seconds by
default), and combat progresses through the turn order, looping through
the participants until the fight ends.

Only simple rolls for attacking are implemented here, but this system
is easily extensible and can be used as the foundation for implementing
the rules from your turn-based tabletop game of choice or making your
own battle system.

To install and test, import this module's TBBasicCharacter object into
your game's character.py module:

    from evennia.contrib.game_systems.turnbattle.tb_basic import TBBasicCharacter

And change your game's character typeclass to inherit from TBBasicCharacter
instead of the default:

    class Character(TBBasicCharacter):

Next, import this module into your default_cmdsets.py module:

    from evennia.contrib.game_systems.turnbattle import tb_basic

And add the battle command set to your default command set:

    #
    # any commands you add below will overload the default ones.
    #
    self.add(tb_basic.BattleCmdSet())

This module is meant to be heavily expanded on, so you may want to copy it
to your game's 'world' folder and modify it there rather than importing it
in your game and using it as-is.
"""

from random import randint

from evennia import Command, DefaultCharacter, DefaultScript, default_cmds
from evennia.commands.default.help import CmdHelp
from evennia.commands.default.muxcommand import MuxCommand
from evennia.prototypes.spawner import spawn
from evennia import TICKER_HANDLER as tickerhandler

from server import appearance

"""
----------------------------------------------------------------------------
OPTIONS
----------------------------------------------------------------------------
"""

TURN_TIMEOUT = 30  # Time before turns automatically end, in seconds
ACTIONS_PER_TURN = 1  # Number of actions allowed per turn
NONCOMBAT_TURN_TIME = 30  # Time per turn count out of combat

# Condition options start here.
# If you need to make changes to how your conditions work later,
# it's best to put the easily tweakable values all in one place!

REGEN_RATE = (4, 8)  # Min and max HP regen for Regeneration
POISON_RATE = (4, 8)  # Min and max damage for Poisoned
ACC_UP_MOD = 25  # Accuracy Up attack roll bonus
ACC_DOWN_MOD = -25  # Accuracy Down attack roll penalty
DMG_UP_MOD = 5  # Damage Up damage roll bonus
DMG_DOWN_MOD = -5  # Damage Down damage roll penalty
DEF_UP_MOD = 15  # Defense Up defense bonus
DEF_DOWN_MOD = -15  # Defense Down defense penalty

"""
----------------------------------------------------------------------------
COMBAT FUNCTIONS START HERE
----------------------------------------------------------------------------
"""


class BasicCombatRules:
    """
    Stores all combat rules and helper methods.

    """

    def roll_init(self, character):
        """
        Rolls a number between 1-1000 to determine initiative.

        Args:
            character (obj): The character to determine initiative for

        Returns:
            initiative (int): The character's place in initiative - higher
            numbers go first.

        Notes:
            By default, does not reference the character and simply returns
            a random integer from 1 to 1000.

            Since the character is passed to this function, you can easily reference
            a character's stats to determine an initiative roll - for example, if your
            character has a 'dexterity' attribute, you can use it to give that character
            an advantage in turn order, like so:

            return (randint(1,20)) + character.db.dexterity

            This way, characters with a higher dexterity will go first more often.
        """
        return randint(1, 20) + character.db.attribs["Dexterity"]

    def get_attack(self, attacker, defender):
        """
        Returns a value for an attack roll.

        Args:
            attacker (obj): Character doing the attacking
            defender (obj): Character being attacked

        Returns:
            attack_value (int): Attack roll value, compared against a defense value
                to determine whether an attack hits or misses.

        Notes:
            In this example, a weapon's accuracy bonus is factored into the attack
            roll. Lighter weapons are more accurate but less damaging, and heavier
            weapons are less accurate but deal more damage. Of course, you can
            change this paradigm completely in your own game.
        """
        # Start with a roll from 1 to 100.
        attack_value = randint(1, 100)
        accuracy_bonus = 0
        # If armed, add weapon's accuracy bonus.
        if attacker.db.wielded_weapon:
            weapon = attacker.db.wielded_weapon
            accuracy_bonus += weapon.db.accuracy_bonus
        # If unarmed, use character's unarmed accuracy bonus.
        """else:
            accuracy_bonus += attacker.db.unarmed_accuracy
        # Add the accuracy bonus to the attack roll."""
        attack_value += accuracy_bonus

        # Add to the roll if the attacker has the "Accuracy Up" condition.
        if "Accuracy Up" in attacker.db.conditions:  # TODO: Rename conditions to effects?
            attack_value += ACC_UP_MOD
        # Subtract from the roll if the attack has the "Accuracy Down" condition.
        if "Accuracy Down" in attacker.db.conditions:
            attack_value += ACC_DOWN_MOD

        return attack_value

    def get_defense(self, attacker, defender):
        """
        Returns a value for defense, which an attack roll must equal or exceed in order
        for an attack to hit.

        Args:
            attacker (obj): Character doing the attacking
            defender (obj): Character being attacked

        Returns:
            defense_value (int): Defense value, compared against an attack roll
                to determine whether an attack hits or misses.

        Notes:
            Characters are given a default defense value of 50 which can be
            modified up or down by armor. In this example, wearing armor actually
            makes you a little easier to hit, but reduces incoming damage.
        """
        # Start with a defense value of 50 for a 50/50 chance to hit.
        defense_value = 50
        # Modify this value based on defender's armor.
        if defender.db.worn_armor:
            armor = defender.db.worn_armor
            defense_value += armor.db.defense_modifier
        return defense_value

    def get_damage(self, attacker, defender):
        """
        Returns a value for damage to be deducted from the defender's HP after abilities
        successful hit.

        Args:
            attacker (obj): Character doing the attacking
            defender (obj): Character being damaged

        Returns:
            damage_value (int): Damage value, which is to be deducted from the defending
                character's HP.

        Notes:
            Damage is determined by the attacker's wielded weapon, or the attacker's
            unarmed damage range if no weapon is wielded. Incoming damage is reduced
            by the defender's armor.
        """
        damage_value = 0
        # Generate a damage value from wielded weapon if armed
        if attacker.db.wielded_weapon:
            weapon = attacker.db.wielded_weapon
            # Roll between minimum and maximum damage
            damage_value = randint(weapon.db.damage_range[0], weapon.db.damage_range[1])
        # Use attacker's unarmed damage otherwise
        else:
            damage_value = randint(
                attacker.db.unarmed_damage_range[0], attacker.db.unarmed_damage_range[1]
            )

        # Add to damage roll if attacker has the "Damage Up" condition.
        if "Damage Up" in attacker.db.conditions:
            damage_value += DMG_UP_MOD
            # Subtract from the roll if the attacker has the "Damage Down" condition.
        if "Damage Down" in attacker.db.conditions:
            damage_value += DMG_DOWN_MOD

        # If defender is armored, reduce incoming damage
        if defender.db.worn_armor:
            armor = defender.db.worn_armor
            damage_value -= armor.db.damage_reduction
        # Make sure minimum damage is 0
        if damage_value < 0:
            damage_value = 0
        return damage_value

    def apply_damage(self, defender, damage):
        """
        Applies damage to a target, reducing their HP by the damage amount to a
        minimum of 0.

        Args:
            defender (obj): Character taking damage
            damage (int): Amount of damage being taken
        """
        defender.db.hp -= damage  # Reduce defender's HP by the damage dealt.
        # If this reduces it to 0 or less, set HP to 0.
        if defender.db.hp <= 0:
            defender.db.hp = 0

    def at_defeat(self, defeated):
        """
        Announces the defeat of a fighter in combat.

        Args:
            defeated (obj): Fighter that's been defeated.

        Notes:
            All this does is announce a defeat message by default, but if you
            want anything else to happen to defeated fighters (like putting them
            into a dying state or something similar) then this is the place to
            do it.
        """
        defeated.location.msg_contents(f"%s{appearance.attention} has been defeated!" % defeated.get_display_name())

    def resolve_attack(self, attacker, defender, attack_value=None, defense_value=None):
        """
        Resolves an attack and outputs the result.

        Args:
            attacker (obj): Character doing the attacking
            defender (obj): Character being attacked

        Notes:
            Even though the attack and defense values are calculated
            extremely simply, they are separated out into their own functions
            so that they are easier to expand upon.
        """
        # Get the attacker's weapon type to reference in combat messages.
        attackers_weapon = "attack"
        if attacker.db.wielded_weapon:
            weapon = attacker.db.wielded_weapon
            attackers_weapon = weapon.db.weapon_type_name
        # Get an attack roll from the attacker.
        if not attack_value:
            attack_value = self.get_attack(attacker, defender)
        # Get a defense value from the defender.
        if not defense_value:
            defense_value = self.get_defense(attacker, defender)
        # If the attack value is lower than the defense value, miss. Otherwise, hit.
        if attack_value < defense_value:
            attacker.location.msg_contents(
                "%s's %s misses %s!" % (attacker.get_display_name(), attackers_weapon, defender)
            )
        else:
            damage_value = self.get_damage(attacker, defender)  # Calculate damage value.
            # Announce damage dealt and apply damage.
            if damage_value > 0:
                attacker.location.msg_contents(
                    "%s's %s strikes %s for %i damage!"
                    % (attacker, attackers_weapon, defender, damage_value)
                )
            else:
                attacker.location.msg_contents(
                    "%s's %s bounces harmlessly off %s!" % (attacker, attackers_weapon, defender)
                )
            self.apply_damage(defender, damage_value)
            # If defender HP is reduced to 0 or less, call at_defeat.
            if defender.db.hp <= 0:
                self.at_defeat(defender)

    def combat_cleanup(self, character):
        """
        Cleans up all the temporary combat-related attributes on a character.

        Args:
            character (obj): Character to have their combat attributes removed

        Notes:
            Any attribute whose key begins with 'combat_' is temporary and no
            longer needed once a fight ends.
        """
        for attr in character.attributes.all():
            if attr.key[:7] == "combat_":  # If the attribute name starts with 'combat_'...
                character.attributes.remove(key=attr.key)  # ...then delete it!

    def is_in_combat(self, character):
        """
        Returns true if the given character is in combat.

        Args:
            character (obj): Character to determine if is in combat or not

        Returns:
            (bool): True if in combat or False if not in combat
        """
        return bool(character.db.combat_turnhandler)

    def is_turn(self, character):
        """
        Returns true if it's currently the given character's turn in combat.

        Args:
            character (obj): Character to determine if it is their turn or not

        Returns:
            (bool): True if it is their turn or False otherwise
        """
        turnhandler = character.db.combat_turnhandler
        currentchar = turnhandler.db.fighters[turnhandler.db.turn]
        return bool(character == currentchar)

    def spend_action(self, character, actions, action_name=None):
        """
        Spends a character's available combat actions and checks for end of turn.

        Args:
            character (obj): Character spending the action
            actions (int) or 'all': Number of actions to spend, or 'all' to spend all actions

        Keyword Args:
            action_name (str or None): If a string is given, sets character's last action in
            combat to provided string
        """
        if action_name:
            character.db.combat_lastaction = action_name
        if actions == "all":  # If spending all actions
            character.db.combat_actionsleft = 0  # Set actions to 0
        else:
            character.db.combat_actionsleft -= actions  # Use up actions.
            if character.db.combat_actionsleft < 0:
                character.db.combat_actionsleft = 0  # Can't have fewer than 0 actions
        character.db.combat_turnhandler.turn_end_check(character)  # Signal potential end of turn.

    # ITEM RULES

    def spend_item_use(self, item, user):
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
        item.db.item_uses -= 1  # Spend one use

        if item.db.item_uses > 0:  # Has uses remaining
            # Inform the player
            user.msg("%s has %i uses remaining." % (item.key.capitalize(), item.db.item_uses))

        else:  # All uses spent
            if not item.db.item_consumable:  # Item isn't consumable
                # Just inform the player that the uses are gone
                user.msg("%s has no uses remaining." % item.key.capitalize())

            else:  # If item is consumable
                # If the value is 'True', just destroy the item
                if item.db.item_consumable:
                    user.msg("%s has been consumed." % item.key.capitalize())
                    item.delete()  # Delete the spent item

                else:  # If a string, use value of item_consumable to spawn an object in its place
                    residue = spawn({"prototype": item.db.item_consumable})[0]  # Spawn the residue
                    # Move the residue to the same place as the item
                    residue.location = item.location
                    user.msg("After using %s, you are left with %s." % (item, residue))
                    item.delete()  # Delete the spent item

    def use_item(self, user, item, target):
        """
        Performs the action of using an item.

        Args:
            user (obj): Character using the item
            item (obj): Item being used
            target (obj): Target of the item use
        """
        # If item is self only and no target given, set target to self.
        if item.db.item_selfonly and target is None:
            target = user

        # If item is self only, abort use if used on others.
        if item.db.item_selfonly and user != target:
            user.msg("%s can only be used on yourself." % item)
            return

        # Set kwargs to pass to item_func
        kwargs = {}
        if item.db.item_kwargs:
            kwargs = item.db.item_kwargs

        # Match item_func string to function
        try:
            item_func = ITEMFUNCS[item.db.item_func]
        except KeyError:  # If item_func string doesn't match to a function in ITEMFUNCS
            user.msg("ERROR: %s not defined in ITEMFUNCS" % item.db.item_func)
            return

        # Call the item function - abort if it returns False, indicating an error.
        # This performs the actual action of using the item.
        # Regardless of what the function returns (if anything), it's still executed.
        if not item_func(item, user, target, **kwargs):
            return

        # If we haven't returned yet, we assume the item was used successfully.
        # Spend one use if item has limited uses
        if item.db.item_uses:
            self.spend_item_use(item, user)

        # Spend an action if in combat
        if self.is_in_combat(user):
            self.spend_action(user, 1, action_name="item")

    def condition_tickdown(self, character, turnchar):
        """
        Ticks down the duration of conditions on a character at the start of a given character's
        turn.

        Args:
            character (obj): Character to tick down the conditions of
            turnchar (obj): Character whose turn it currently is

        Notes:
            In combat, this is called on every fighter at the start of every character's turn. Out
            of combat, it's instead called when a character's at_update() hook is called, which is
            every 30 seconds by default.
        """

        for key in character.db.conditions:
            # The first value is the remaining turns - the second value is whose turn to count down
            # on.
            condition_duration = character.db.conditions[key][0]
            condition_turnchar = character.db.conditions[key][1]
            # If the duration is 'True', then the condition doesn't tick down - it lasts
            # indefinitely.
            if condition_duration is not True:
                # Count down if the given turn character matches the condition's turn character.
                if condition_turnchar == turnchar:
                    character.db.conditions[key][0] -= 1
                if character.db.conditions[key][0] <= 0:
                    # If the duration is brought down to 0, remove the condition and inform
                    # everyone.
                    character.location.msg_contents(
                        "%s no longer has the '%s' condition." % (str(character), str(key))
                    )
                    del character.db.conditions[key]

    def add_condition(self, character, turnchar, condition, duration):
        """
        Adds a condition to a fighter.

        Args:
            character (obj): Character to give the condition to
            turnchar (obj): Character whose turn to tick down the condition on in combat
            condition (str): Name of the condition
            duration (int or True): Number of turns the condition lasts, or True for indefinite
        """
        # The first value is the remaining turns - the second value is whose turn to count down on.
        character.db.conditions.update({condition: [duration, turnchar]})
        # Tell everyone!
        character.location.msg_contents("%s gains the '%s' condition." % (character, condition))

    # ----------------------------------------------------------------------------
    # ITEM FUNCTIONS START HERE
    # ----------------------------------------------------------------------------

    # These functions carry out the action of using an item - every item should
    # contain a db entry "item_func", with its value being a string that is
    # matched to one of these functions in the ITEMFUNCS dictionary below.

    # Every item function must take the following arguments:
    #     item (obj): The item being used
    #     user (obj): The character using the item
    #     target (obj): The target of the item use

    # Item functions must also accept **kwargs - these keyword arguments can be
    # used to define how different items that use the same function can have
    # different effects (for example, different attack items doing different
    # amounts of damage).

    # Each function below contains a description of what kwargs the function will
    # take and the effect they have on the result.

    def itemfunc_heal(self, item, user, target, **kwargs):
        """
        Item function that heals HP.

        kwargs:
            min_healing(int): Minimum amount of HP recovered
            max_healing(int): Maximum amount of HP recovered
        """
        if not target:
            target = user  # Target user if none specified

        if not target.attributes.has("max_hp"):  # Has no HP to speak of
            user.msg("You can't use %s on that." % item)
            return False  # Returning false aborts the item use

        if target.db.hp >= target.db.max_hp:
            user.msg("%s is already at full health." % target)
            return False

        min_healing = 20
        max_healing = 40

        # Retrieve healing range from kwargs, if present
        if "healing_range" in kwargs:
            min_healing = kwargs["healing_range"][0]
            max_healing = kwargs["healing_range"][1]

        to_heal = randint(min_healing, max_healing)  # Restore 20 to 40 hp
        if target.db.hp + to_heal > target.db.max_hp:
            to_heal = target.db.max_hp - target.db.hp  # Cap healing to max HP
        target.db.hp += to_heal

        user.location.msg_contents("%s uses %s! %s regains %i HP!" % (user, item, target, to_heal))

    def itemfunc_add_condition(self, item, user, target, **kwargs):
        """
        Item function that gives the target one or more conditions.

        kwargs:
            conditions (list): Conditions added by the item
               formatted as a list of tuples: (condition (str), duration (int or True))

        Notes:
            Should mostly be used for beneficial conditions - use itemfunc_attack
            for an item that can give an enemy a harmful condition.
        """
        conditions = [("Regeneration", 5)]

        if not target:
            target = user  # Target user if none specified

        if not target.attributes.has("max_hp"):  # Is not a fighter
            user.msg("You can't use %s on that." % item)
            return False  # Returning false aborts the item use

        # Retrieve condition / duration from kwargs, if present
        if "conditions" in kwargs:
            conditions = kwargs["conditions"]

        user.location.msg_contents("%s uses %s!" % (user, item))

        # Add conditions to the target
        for condition in conditions:
            self.add_condition(target, user, condition[0], condition[1])

    def itemfunc_cure_condition(self, item, user, target, **kwargs):
        """
        Item function that'll remove given conditions from a target.

        kwargs:
            to_cure(list): List of conditions (str) that the item cures when used
        """
        to_cure = ["Poisoned"]

        if not target:
            target = user  # Target user if none specified

        if not target.attributes.has("max_hp"):  # Is not a fighter
            user.msg("You can't use %s on that." % item)
            return False  # Returning false aborts the item use

        # Retrieve condition(s) to cure from kwargs, if present
        if "to_cure" in kwargs:
            to_cure = kwargs["to_cure"]

        item_msg = "%s uses %s! " % (user, item)

        for key in target.db.conditions:
            if key in to_cure:
                # If condition specified in to_cure, remove it.
                item_msg += "%s no longer has the '%s' condition. " % (str(target), str(key))
                del target.db.conditions[key]

        user.location.msg_contents(item_msg)

    def itemfunc_attack(self, item, user, target, **kwargs):
        """
        Item function that attacks a target.

        kwargs:
            min_damage(int): Minimum damage dealt by the attack
            max_damage(int): Maximum damage dealth by the attack
            accuracy(int): Bonus / penalty to attack accuracy roll
            inflict_condition(list): List of conditions inflicted on hit,
                formatted as a (str, int) tuple containing condition name
                and duration.

        Notes:
            Calls resolve_attack at the end.
        """
        if not self.is_in_combat(user):
            user.msg("You can only use that in combat.")
            return False  # Returning false aborts the item use

        if not target:
            user.msg("You have to specify a target to use %s! (use <item> = <target>)" % item)
            return False

        if target == user:
            user.msg("You can't attack yourself!")
            return False

        if not target.db.hp:  # Has no HP
            user.msg("You can't use %s on that." % item)
            return False

        min_damage = 20
        max_damage = 40
        accuracy = 0
        inflict_condition = []

        # Retrieve values from kwargs, if present
        if "damage_range" in kwargs:
            min_damage = kwargs["damage_range"][0]
            max_damage = kwargs["damage_range"][1]
        if "accuracy" in kwargs:
            accuracy = kwargs["accuracy"]
        if "inflict_condition" in kwargs:
            inflict_condition = kwargs["inflict_condition"]

        # Roll attack and damage
        attack_value = randint(1, 100) + accuracy
        damage_value = randint(min_damage, max_damage)

        # Account for "Accuracy Up" and "Accuracy Down" conditions
        if "Accuracy Up" in user.db.conditions:
            attack_value += 25
        if "Accuracy Down" in user.db.conditions:
            attack_value -= 25

        user.location.msg_contents("%s attacks %s with %s!" % (user, target, item))
        self.resolve_attack(
            user,
            target,
            attack_value=attack_value,
            damage_value=damage_value,
            inflict_condition=inflict_condition,
        )


COMBAT_RULES = BasicCombatRules()

"""
----------------------------------------------------------------------------
PROTOTYPES START HERE
----------------------------------------------------------------------------

You can paste these prototypes into your game's prototypes.py module in your
/world/ folder, and use the spawner to create them - they serve as examples
of items you can make and a handy way to demonstrate the system for
conditions as well.

Items don't have any particular typeclass - any object with a db entry
"item_func" that references one of the functions given above can be used as
an item with the 'use' command.

Only "item_func" is required, but item behavior can be further modified by
specifying any of the following:

    item_uses (int): If defined, item has a limited number of uses

    item_selfonly (bool): If True, user can only use the item on themself

    item_consumable(True or str): If True, item is destroyed when it runs
        out of uses. If a string is given, the item will spawn a new
        object as it's destroyed, with the string specifying what prototype
        to spawn.

    item_kwargs (dict): Keyword arguments to pass to the function defined in
        item_func. Unique to each function, and can be used to make multiple
        items using the same function work differently.
"""
ITEMFUNCS = {
    "heal": COMBAT_RULES.itemfunc_heal,
    "attack": COMBAT_RULES.itemfunc_attack,
    "add_condition": COMBAT_RULES.itemfunc_add_condition,
    "cure_condition": COMBAT_RULES.itemfunc_cure_condition,
}

"""
----------------------------------------------------------------------------
PROTOTYPES START HERE
----------------------------------------------------------------------------

You can paste these prototypes into your game's prototypes.py module in your
/world/ folder, and use the spawner to create them - they serve as examples
of items you can make and a handy way to demonstrate the system for
conditions as well.

Items don't have any particular typeclass - any object with a db entry
"item_func" that references one of the functions given above can be used as
an item with the 'use' command.

Only "item_func" is required, but item behavior can be further modified by
specifying any of the following:

    item_uses (int): If defined, item has a limited number of uses

    item_selfonly (bool): If True, user can only use the item on themself

    item_consumable(True or str): If True, item is destroyed when it runs
        out of uses. If a string is given, the item will spawn a new
        object as it's destroyed, with the string specifying what prototype
        to spawn.

    item_kwargs (dict): Keyword arguments to pass to the function defined in
        item_func. Unique to each function, and can be used to make multiple
        items using the same function work differently.
"""

MEDKIT = {
    "key": "a medical kit",
    "aliases": ["medkit"],
    "desc": "A standard medical kit. It can be used a few times to heal wounds.",
    "item_func": "heal",
    "item_uses": 3,
    "item_consumable": True,
    "item_kwargs": {"healing_range": (15, 25)},
}

GLASS_BOTTLE = {"key": "a glass bottle", "desc": "An empty glass bottle."}

HEALTH_POTION = {
    "key": "a health potion",
    "desc": "A glass bottle full of a mystical potion that heals wounds when used.",
    "item_func": "heal",
    "item_uses": 1,
    "item_consumable": "GLASS_BOTTLE",
    "item_kwargs": {"healing_range": (35, 50)},
}

REGEN_POTION = {
    "key": "a regeneration potion",
    "desc": "A glass bottle full of a mystical potion that regenerates wounds over time.",
    "item_func": "add_condition",
    "item_uses": 1,
    "item_consumable": "GLASS_BOTTLE",
    "item_kwargs": {"conditions": [("Regeneration", 10)]},
}

HASTE_POTION = {
    "key": "a haste potion",
    "desc": "A glass bottle full of a mystical potion that hastens its user.",
    "item_func": "add_condition",
    "item_uses": 1,
    "item_consumable": "GLASS_BOTTLE",
    "item_kwargs": {"conditions": [("Haste", 10)]},
}

BOMB = {
    "key": "a rotund bomb",
    "desc": "A large black sphere with a fuse at the end. Can be used on enemies in combat.",
    "item_func": "attack",
    "item_uses": 1,
    "item_consumable": True,
    "item_kwargs": {"damage_range": (25, 40), "accuracy": 25},
}

POISON_DART = {
    "key": "a poison dart",
    "desc": "A thin dart coated in deadly poison. Can be used on enemies in combat",
    "item_func": "attack",
    "item_uses": 1,
    "item_consumable": True,
    "item_kwargs": {
        "damage_range": (5, 10),
        "accuracy": 25,
        "inflict_condition": [("Poisoned", 10)],
    },
}

TASER = {
    "key": "a taser",
    "desc": "A device that can be used to paralyze enemies in combat.",
    "item_func": "attack",
    "item_kwargs": {
        "damage_range": (10, 20),
        "accuracy": 0,
        "inflict_condition": [("Paralyzed", 1)],
    },
}

GHOST_GUN = {
    "key": "a ghost gun",
    "desc": "A gun that fires scary ghosts at people. Anyone hit by a ghost becomes frightened.",
    "item_func": "attack",
    "item_uses": 6,
    "item_kwargs": {
        "damage_range": (5, 10),
        "accuracy": 15,
        "inflict_condition": [("Frightened", 1)],
    },
}

ANTIDOTE_POTION = {
    "key": "an antidote potion",
    "desc": "A glass bottle full of a mystical potion that cures poison when used.",
    "item_func": "cure_condition",
    "item_uses": 1,
    "item_consumable": "GLASS_BOTTLE",
    "item_kwargs": {"to_cure": ["Poisoned"]},
}

AMULET_OF_MIGHT = {
    "key": "The Amulet of Might",
    "desc": "The one who holds this amulet can call upon its power to gain great strength.",
    "item_func": "add_condition",
    "item_selfonly": True,
    "item_kwargs": {"conditions": [("Damage Up", 3), ("Accuracy Up", 3), ("Defense Up", 3)]},
}

AMULET_OF_WEAKNESS = {
    "key": "The Amulet of Weakness",
    "desc": "The one who holds this amulet can call upon its power to gain great weakness. "
            "It's not a terribly useful artifact.",
    "item_func": "add_condition",
    "item_selfonly": True,
    "item_kwargs": {"conditions": [("Damage Down", 3), ("Accuracy Down", 3), ("Defense Down", 3)]},
}

"""
----------------------------------------------------------------------------
CHARACTER TYPECLASS
----------------------------------------------------------------------------
"""


class TurnBattleCharacter(DefaultCharacter):
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
        self.db.max_hp = 100  # Set maximum HP to 100
        self.db.hp = self.db.max_hp  # Set current HP to maximum

        self.db.wielded_weapon = None  # Currently used weapon
        self.db.worn_armor = None  # Currently worn armor
        self.db.unarmed_damage_range = (5, 15)  # Minimum and maximum unarmed damage
        self.db.unarmed_accuracy = 30  # Accuracy bonus for unarmed attacks

        self.db.conditions = {}  # Set empty dict for conditions

        # Subscribe character to the ticker handler
        tickerhandler.add(NONCOMBAT_TURN_TIME, self.at_update, idstring="update")
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
        if "Regeneration" in self.db.conditions:
            to_heal = randint(REGEN_RATE[0], REGEN_RATE[1])  # Restore HP
            if self.db.hp + to_heal > self.db.max_hp:
                to_heal = self.db.max_hp - self.db.hp  # Cap healing to max HP
            self.db.hp += to_heal
            self.location.msg_contents("%s regains %i HP from Regeneration." % (self, to_heal))

        # Poisoned: does 4 to 8 damage at the start of character's turn
        if "Poisoned" in self.db.conditions:
            to_hurt = randint(POISON_RATE[0], POISON_RATE[1])  # Deal damage
            self.rules.apply_damage(self, to_hurt)
            self.location.msg_contents("%s takes %i damage from being Poisoned." % (self, to_hurt))
            if self.db.hp <= 0:
                # Call at_defeat if poison defeats the character
                self.rules.at_defeat(self)

        # Haste: Gain an extra action in combat.
        if self.rules.is_in_combat(self) and "Haste" in self.db.conditions:
            self.db.combat_actionsleft += 1
            self.msg("You gain an extra action this turn from Haste!")

        # Paralyzed: Have no actions in combat.
        if self.rules.is_in_combat(self) and "Paralyzed" in self.db.conditions:
            self.db.combat_actionsleft = 0
            self.location.msg_contents("%s is Paralyzed, and can't act this turn!" % self)
            self.db.combat_turnhandler.turn_end_check(self)

    def at_update(self):
        """
        Fires every 30 seconds.
        """
        if not self.rules.is_in_combat(self):  # Not in combat
            # Change all conditions to update on character's turn.
            for key in self.db.conditions:
                self.db.conditions[key][1] = self
            # Apply conditions that fire every turn
            self.apply_turn_conditions()
            # Tick down condition durations
            self.rules.condition_tickdown(self, self)


"""
----------------------------------------------------------------------------
SCRIPTS START HERE
----------------------------------------------------------------------------
"""


class TurnHandler(DefaultScript):
    """
    This is the script that handles the progression of combat through turns.
    On creation (when a fight is started) it adds all combat-ready characters
    to its roster and then sorts them into a turn order. There can only be one
    fight going on in a single room at a time, so the script is assigned to a
    room as its object.

    Fights persist until only one participant is left with any HP or all
    remaining participants choose to end the combat with the 'disengage' command.
    """

    rules = COMBAT_RULES

    def at_script_creation(self):
        """
        Called once, when the script is created.
        """
        self.key = "Combat Turn Handler"
        self.interval = 5  # Once every 5 seconds
        self.persistent = True
        self.db.fighters = []

        # Add all fighters in the room with at least 1 HP to the combat."
        for thing in self.obj.contents:
            if thing.db.hp:
                self.db.fighters.append(thing)

        # Initialize each fighter for combat
        for fighter in self.db.fighters:
            self.initialize_for_combat(fighter)

        # Add a reference to this script to the room
        self.obj.db.combat_turnhandler = self

        # Roll initiative and sort the list of fighters depending on who rolls highest to determine
        # turn order.  The initiative roll is determined by the roll_init method and can be
        # customized easily.
        ordered_by_roll = sorted(self.db.fighters, key=self.rules.roll_init, reverse=True)
        self.db.fighters = ordered_by_roll

        # Announce the turn order.
        self.obj.msg_contents("Turn order is: %s " % ", ".join(obj.get_display_name() for obj in self.db.fighters))

        # Start first fighter's turn.
        self.start_turn(self.db.fighters[0])

        # Set up the current turn and turn timeout delay.
        self.db.turn = 0
        self.db.timer = TURN_TIMEOUT  # Set timer to turn timeout specified in options

    def at_stop(self):
        """
        Called at script termination.
        """
        for fighter in self.db.fighters:
            if fighter:
                # Clean up the combat attributes for every fighter.
                self.rules.combat_cleanup(fighter)
        self.obj.db.combat_turnhandler = None  # Remove reference to turn handler in location

    def at_repeat(self):
        """
        Called once every self.interval seconds.
        """
        currentchar = self.db.fighters[
            self.db.turn
        ]  # Note the current character in the turn order.
        self.db.timer -= self.interval  # Count down the timer.

        if self.db.timer <= 0:
            # Force current character to disengage if timer runs out.
            self.obj.msg_contents("%s's turn timed out!" % currentchar.get_display_name())
            self.rules.spend_action(
                currentchar, "all", action_name="disengage"
            )  # Spend all remaining actions.
            return
        elif self.db.timer <= 10 and not self.db.timeout_warning_given:  # 10 seconds left
            # Warn the current character if they're about to time out.
            currentchar.msg(f"{appearance.warning}WARNING: About to time out!")
            self.db.timeout_warning_given = True

    def initialize_for_combat(self, character):
        """
        Prepares a character for combat when starting or entering a fight.

        Args:
            character (obj): Character to initialize for combat.
        """
        # Clean up leftover combat attributes beforehand, just in case.
        self.rules.combat_cleanup(character)
        character.db.combat_actionsleft = (
            0  # Actions remaining - start of turn adds to this, turn ends when it reaches 0
        )
        character.db.combat_turnhandler = (
            self  # Add a reference to this turn handler script to the character
        )
        character.db.combat_lastaction = "null"  # Track last action taken in combat

    def start_turn(self, character):
        """
        Readies a character for the start of their turn by replenishing their
        available actions and notifying them that their turn has come up.

        Args:
            character (obj): Character to be readied.

        Notes:
            Here, you only get one action per turn, but you might want to allow more than
            one per turn, or even grant a number of actions based on a character's
            attributes. You can even add multiple different kinds of actions, I.E. actions
            separated for movement, by adding "character.db.combat_movesleft = 3" or
            something similar.
        """
        character.apply_turn_conditions()

        character.db.combat_actionsleft = ACTIONS_PER_TURN  # Replenish actions

        other_fighters = self.obj.contents
        other_fighters.remove(character)
        if character.db.hostile:
            msg = "|[100"
        else:
            msg = "|[010"
        msg = msg + ("~~~ %s's Turn ~~~" % (character.name))
        for obj in other_fighters:
            obj.msg(msg)

        # Prompt the character for their turn and give some information.
        character.msg("|[550|=a~~~~~ YOUR TURN ~~~~~~")
        character.msg("|wYou have %i HP remaining.|n" % character.db.hp)

    def next_turn(self):
        """
        Advances to the next character in the turn order.
        """

        # Check to see if every character disengaged as their last action. If so, end combat.
        disengage_check = True
        for fighter in self.db.fighters:
            if (
                    fighter.db.combat_lastaction != "disengage"
            ):  # If a character has done anything but disengage
                disengage_check = False
        if disengage_check:  # All characters have disengaged
            self.obj.msg_contents("All fighters have disengaged! Combat is over!")
            self.stop()  # Stop this script and end combat.
            self.delete()
            return

        # Check if all left standing are either hostile or friendly
        hostiles_left = 0
        nonhostiles_left = 0
        for fighter in self.db.fighters:
            if fighter.db.hp > 0:
                if fighter.db.hostile:
                    hostiles_left += 1
                else:
                    nonhostiles_left += 1
        if (hostiles_left == 0) or (nonhostiles_left == 0):
            self.obj.msg_contents(f"{appearance.ambient}Quiet falls upon the battlefield.")
            if hostiles_left == 0:
                self.obj.msg_contents("|[050|=aYou are victorious!")
            self.stop()  # Stop this script and end combat.
            self.delete()
            return

        # Cycle to the next turn.
        currentchar = self.db.fighters[self.db.turn]
        self.db.turn += 1  # Go to the next in the turn order.
        if self.db.turn > len(self.db.fighters) - 1:
            self.db.turn = 0  # Go back to the first in the turn order once you reach the end.
        newchar = self.db.fighters[self.db.turn]  # Note the new character
        self.db.timer = TURN_TIMEOUT + self.time_until_next_repeat()  # Reset the timer.
        self.db.timeout_warning_given = False  # Reset the timeout warning.

        self.start_turn(newchar)  # Start the new character's turn.

        # Count down condition timers.
        next_fighter = self.db.fighters[self.db.turn]
        for fighter in self.db.fighters:
            self.rules.condition_tickdown(fighter, next_fighter)

    def turn_end_check(self, character):
        """
        Tests to see if a character's turn is over, and cycles to the next turn if it is.

        Args:
            character (obj): Character to test for end of turn
        """
        if not character.db.combat_actionsleft:  # Character has no actions remaining
            self.next_turn()
            return

    def join_fight(self, character):
        """
        Adds a new character to a fight already in progress.

        Args:
            character (obj): Character to be added to the fight.
        """
        # Inserts the fighter to the turn order, right behind whoever's turn it currently is.
        self.db.fighters.insert(self.db.turn, character)
        # Tick the turn counter forward one to compensate.
        self.db.turn += 1
        # Initialize the character like you do at the start.
        self.initialize_for_combat(character)


"""
----------------------------------------------------------------------------
COMMANDS START HERE
----------------------------------------------------------------------------
"""


class CmdFight(Command):
    """
    Starts a fight with everyone in the same room as you.

    Usage:
      fight

    When you start a fight, everyone in the room who is able to
    fight is added to combat, and a turn order is randomly rolled.
    When it's your turn, you can attack other characters.
    """

    key = "fight"
    help_category = "combat"

    rules = COMBAT_RULES
    combat_handler_class = TurnHandler

    def func(self):
        """
        This performs the actual command.
        """
        here = self.caller.location
        fighters = []

        if not self.caller.db.hp:  # If you don't have any hp
            self.caller.msg("You can't start a fight if you've been defeated!")
            return
        if self.rules.is_in_combat(self.caller):  # Already in a fight
            self.caller.msg("You're already in a fight!")
            return
        # TODO: Take hostility into account instead of just starting a fight with everyone
        for thing in here.contents:  # Test everything in the room to add it to the fight.
            if thing.db.HP:  # If the object has HP...
                fighters.append(thing)  # ...then add it to the fight.
        if len(fighters) <= 1:  # If you're the only able fighter in the room
            self.caller.msg("There's nobody here to fight!")
            return
        if here.db.combat_turnhandler:  # If there's already a fight going on...
            here.msg_contents("%s joins the fight!" % self.caller.get_display_name())
            here.db.combat_turnhandler.join_fight(self.caller)  # Join the fight!
            return
        here.msg_contents("%s starts a fight!" % self.caller.get_display_name())
        # Add a turn handler script to the room, which starts combat.
        here.scripts.add(self.combat_handler_class)


class CmdAttack(Command):
    """
    Attacks another character.

    Usage:
      attack <target>

    When in a fight, you may attack another character. The attack has
    a chance to hit, and if successful, will deal damage.
    """

    key = "attack"
    aliases = ["att", "hit"]
    help_category = "combat"

    rules = COMBAT_RULES

    def func(self):
        "This performs the actual command."
        "Set the attacker to the caller and the defender to the target."

        if not self.rules.is_in_combat(self.caller):  # If not in combat, can't attack.
            self.caller.msg("You can only do that in combat. (see: help fight)")
            return

        if not self.rules.is_turn(self.caller):  # If it's not your turn, can't attack.
            self.caller.msg("You can only do that on your turn.")
            return

        if not self.caller.db.hp:  # Can't attack if you have no HP.
            self.caller.msg("You can't attack, you've been defeated.")
            return

        attacker = self.caller
        defender = self.caller.search(self.args)

        if not defender:  # No valid target given.
            return

        if not defender.db.hp:  # Target object has no HP left or to begin with
            self.caller.msg("You can't fight that!")
            return

        if attacker == defender:  # Target and attacker are the same
            self.caller.msg("You can't attack yourself!")
            return

        "If everything checks out, call the attack resolving function."
        self.rules.resolve_attack(attacker, defender)
        self.rules.spend_action(self.caller, 1, action_name="attack")  # Use up one action.


class CmdPass(Command):
    """
    Passes on your turn.

    Usage:
      pass

    When in a fight, you can use this command to end your turn early, even
    if there are still any actions you can take.
    """

    key = "pass"
    aliases = ["wait", "hold"]
    help_category = "combat"

    rules = COMBAT_RULES

    def func(self):
        """
        This performs the actual command.
        """
        if not self.rules.is_in_combat(self.caller):  # Can only pass a turn in combat.
            self.caller.msg("You can only do that in combat. (see: help fight)")
            return

        if not self.rules.is_turn(self.caller):  # Can only pass if it's your turn.
            self.caller.msg("You can only do that on your turn.")
            return

        self.caller.location.msg_contents(
            "%s takes no further action, passing the turn." % self.caller
        )
        # Spend all remaining actions.
        self.rules.spend_action(self.caller, "all", action_name="pass")


class CmdDisengage(Command):
    """
    Passes your turn and attempts to end combat.

    Usage:
      disengage

    Ends your turn early and signals that you're trying to end
    the fight. If all participants in a fight disengage, the
    fight ends.
    """

    key = "disengage"
    aliases = ["spare"]
    help_category = "combat"

    rules = COMBAT_RULES

    def func(self):
        """
        This performs the actual command.
        """
        if not self.rules.is_in_combat(self.caller):  # If you're not in combat
            self.caller.msg("You can only do that in combat. (see: help fight)")
            return

        if not self.rules.is_turn(self.caller):  # If it's not your turn
            self.caller.msg("You can only do that on your turn.")
            return

        self.caller.location.msg_contents("%s disengages, ready to stop fighting." % self.caller)
        # Spend all remaining actions.
        self.rules.spend_action(self.caller, "all", action_name="disengage")
        """
        The action_name kwarg sets the character's last action to "disengage", which is checked by
        the turn handler script to see if all fighters have disengaged.
        """


class CmdRest(Command):
    """
    Recovers damage.

    Usage:
      rest

    Resting recovers your HP to its maximum, but you can only
    rest if you're not in a fight.
    """

    key = "rest"
    help_category = "combat"

    rules = COMBAT_RULES

    def func(self):
        "This performs the actual command."

        if self.rules.is_in_combat(self.caller):  # If you're in combat
            self.caller.msg("You can't rest while you're in combat.")
            return

        self.caller.db.hp = self.caller.db.max_hp  # Set current HP to maximum
        self.caller.location.msg_contents("%s rests to recover HP." % self.caller)
        """
        You'll probably want to replace this with your own system for recovering HP.
        """


class CmdCombatHelp(CmdHelp):
    """
    View help or a list of topics

    Usage:
      help <topic or command>
      help list
      help all

    This will search for help on commands and other
    topics related to the game.
    """

    rules = COMBAT_RULES
    combat_help_text = (
        "Available combat commands:|/"
        "|wAttack:|n Attack a target, attempting to deal damage.|/"
        "|wPass:|n Pass your turn without further action.|/"
        "|wDisengage:|n End your turn and attempt to end combat.|/"
    )

    # Just like the default help command, but will give quick
    # tips on combat when used in a fight with no arguments.

    def func(self):
        # In combat and entered 'help' alone
        if self.rules.is_in_combat(self.caller) and not self.args:
            self.caller.msg(self.combat_help_text)
        else:
            super().func()  # Call the default help command


class CmdUse(MuxCommand):
    """
    Use an item.

    Usage:
      use <item> [= target]

    An item can have various function - looking at the item may
    provide information as to its effects. Some items can be used
    to attack others, and as such can only be used in combat.
    """

    key = "use"
    help_category = "combat"

    rules = COMBAT_RULES

    def func(self):
        """
        This performs the actual command.
        """
        # Search for item
        item = self.caller.search(self.lhs, candidates=self.caller.contents)
        if not item:
            return

        # Search for target, if any is given
        target = None
        if self.rhs:
            target = self.caller.search(self.rhs)
            if not target:
                return

        # If in combat, can only use items on your turn
        if self.rules.is_in_combat(self.caller):
            if not self.rules.is_turn(self.caller):
                self.caller.msg("You can only use items on your turn.")
                return

        if not item.db.item_func:  # Object has no item_func, not usable
            self.caller.msg("'%s' is not a usable item." % item.key.capitalize())
            return

        if item.attributes.has("item_uses"):  # Item has limited uses
            if item.db.item_uses <= 0:  # Limited uses are spent
                self.caller.msg("'%s' has no uses remaining." % item.key.capitalize())
                return

        # If everything checks out, call the use_item function
        self.rules.use_item(self.caller, item, target)


class CmdWield(Command):
    """
    Wield a weapon you are carrying

    Usage:
      wield <weapon>

    Select a weapon you are carrying to wield in combat. If
    you are already wielding another weapon, you will switch
    to the weapon you specify instead. Using this command in
    combat will spend your action for your turn. Use the
    "unwield" command to stop wielding any weapon you are
    currently wielding.
    """

    key = "wield"
    help_category = "combat"

    rules = COMBAT_RULES

    def func(self):
        """
        This performs the actual command.
        """
        # If in combat, check to see if it's your turn.
        if self.rules.is_in_combat(self.caller):
            if not self.rules.is_turn(self.caller):
                self.caller.msg("You can only do that on your turn.")
                return
        if not self.args:
            self.caller.msg("Usage: wield <obj>")
            return
        weapon = self.caller.search(self.args, candidates=self.caller.contents)
        if not weapon:
            return
        if not weapon.is_typeclass(
                "evennia.contrib.game_systems.turnbattle.tb_equip.TBEWeapon", exact=True
        ):
            self.caller.msg("That's not a weapon!")
            # Remember to update the path to the weapon typeclass if you move this module!
            return

        if not self.caller.db.wielded_weapon:
            self.caller.db.wielded_weapon = weapon
            self.caller.location.msg_contents("%s wields %s." % (self.caller, weapon))
        else:
            old_weapon = self.caller.db.wielded_weapon
            self.caller.db.wielded_weapon = weapon
            self.caller.location.msg_contents(
                "%s lowers %s and wields %s." % (self.caller, old_weapon, weapon)
            )
        # Spend an action if in combat.
        if self.rules.is_in_combat(self.caller):
            self.rules.spend_action(self.caller, 1, action_name="wield")  # Use up one action.


class CmdUnwield(Command):
    """
    Stop wielding a weapon.

    Usage:
      unwield

    After using this command, you will stop wielding any
    weapon you are currently wielding and become unarmed.
    """

    key = "unwield"
    help_category = "combat"

    rules = COMBAT_RULES

    def func(self):
        """
        This performs the actual command.
        """
        # If in combat, check to see if it's your turn.
        if self.rules.is_in_combat(self.caller):
            if not self.rules.is_turn(self.caller):
                self.caller.msg("You can only do that on your turn.")
                return
        if not self.caller.db.wielded_weapon:
            self.caller.msg("You aren't wielding a weapon!")
        else:
            old_weapon = self.caller.db.wielded_weapon
            self.caller.db.wielded_weapon = None
            self.caller.location.msg_contents("%s lowers %s." % (self.caller, old_weapon))


class BattleCmdSet(default_cmds.CharacterCmdSet):
    """
    This command set includes all the commmands used in the battle system.
    """

    key = "DefaultCharacter"

    def at_cmdset_creation(self):
        """
        Populates the cmdset
        """
        self.add(CmdFight())
        self.add(CmdAttack())
        self.add(CmdRest())
        self.add(CmdPass())
        self.add(CmdDisengage())
        self.add(CmdCombatHelp())
