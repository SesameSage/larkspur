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

from evennia import DefaultScript

from server import appearance
from turnbattle.rules import TURN_TIMEOUT, ACTIONS_PER_TURN, COMBAT_RULES

"""
----------------------------------------------------------------------------
OPTIONS
----------------------------------------------------------------------------
"""

# TODO: Current turn doesn't end if you win (at least via poison dart use)

# Condition options start here.
# If you need to make changes to how your conditions work later,
# it's best to put the easily tweakable values all in one place!


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
