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

from evennia import DefaultScript
from evennia.utils import evtable, inherits_from, delay

from server import appearance
from combat.effects import SECS_PER_TURN, DurationEffect, EffectScript

"""
----------------------------------------------------------------------------
OPTIONS
----------------------------------------------------------------------------
"""

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

TURN_TIMEOUT = 30  # Time before turns automatically end, in seconds
ACTIONS_PER_TURN = 1  # Number of actions allowed per turn
NONCOMBAT_TURN_TIME = 30  # Time per turn count out of combat


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

    def at_script_creation(self):
        """
        Called once, when the script is created.
        """
        super().at_script_creation()
        self.key = "Combat Turn Handler"
        self.interval = 5  # Once every 5 seconds
        self.persistent = True
        self.db.fighters = []
        self.db.starter = None

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
        ordered_by_roll = sorted(self.db.fighters, key=self.roll_init, reverse=True)
        self.db.fighters = ordered_by_roll

        # Set up the current turn and turn timeout delay.
        self.db.turn = 0
        self.db.timer = TURN_TIMEOUT  # Set timer to turn timeout specified in options

    def at_start(self, **kwargs):
        self.roll_turn_order()

        # Push the fight starter to the beginning
        self.db.fighters.remove(self.db.starter)
        self.db.fighters.insert(0, self.db.starter)

        # Start first fighter's turn.
        self.start_turn(self.db.fighters[0])

    def at_stop(self):
        """
        Called at script termination.
        """
        for fighter in self.db.fighters:
            if fighter:
                # Clean up the combat attributes for every fighter.
                self.combat_cleanup(fighter)
        self.obj.db.combat_turnhandler = None  # Remove reference to turn handler in location

    def at_repeat(self):
        """
        Called once every self.interval seconds.
        """
        currentchar = self.db.fighters[
            self.db.turn
        ]  # Note the current character in the turn order.
        self.db.timer -= self.interval  # Count down the timer.
        """self.all_defeat_check()"""

        if self.db.timer <= 0:
            # Force current character to disengage if timer runs out.
            self.obj.msg_contents("%s's turn timed out!" % currentchar.get_display_name(capital=True))
            self.spend_action(
                currentchar, "all", action_name="disengage"
            )  # Spend all remaining actions.
            return
        elif self.db.timer <= 10 and not self.db.timeout_warning_given:  # 10 seconds left
            # Warn the current character if they're about to time out.
            currentchar.msg(f"{appearance.warning}WARNING: About to time out!")
            self.db.timeout_warning_given = True

    def roll_turn_order(self):
        # Roll initiative and sort the list of fighters depending on who rolls highest to determine
        # turn order.  The initiative roll is determined by the roll_init method and can be
        # customized easily.
        ordered_by_roll = sorted(self.db.fighters, key=self.roll_init, reverse=True)
        self.db.fighters = ordered_by_roll
        self.db.fighters.remove(self.db.starter)
        self.db.fighters.insert(0, self.db.starter)

        # Announce the turn order.
        self.obj.msg_contents(
            "Turn order is: %s " % ", ".join(obj.get_display_name(capital=True) for obj in self.db.fighters))

    def initialize_for_combat(self, character):
        """
        Prepares a character for combat when starting or entering a fight.

        Args:
            character (obj): Character to initialize for combat.
        """
        # Clean up leftover combat attributes beforehand, just in case.
        self.combat_cleanup(character)
        character.db.combat_actionsleft = (
            0  # Actions remaining - start of turn adds to this, turn ends when it reaches 0
        )
        character.db.combat_turnhandler = (
            self  # Add a reference to this turn handler script to the character
        )
        character.db.combat_lastaction = "null"  # Track last action taken in combat

    def is_in_combat(self, character):
        """
        Returns true if the given character is in combat.

        Args:
            character (obj): Character to determine if is in combat or not

        Returns:
            (bool): True if in combat or False if not in combat
        """
        return bool(character.db.combat_turnhandler)

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
        return randint(1, 20) + character.get_attr("dex")

    def count_hostiles(self):
        """Returns a tuple with the numbers of hostiles and nonhostiles remaining in battle."""
        hostiles_left = 0
        nonhostiles_left = 0
        for fighter in self.db.fighters:
            if fighter.db.hp > 0:
                if fighter.db.hostile_to_players:
                    hostiles_left += 1
                else:
                    nonhostiles_left += 1
        return hostiles_left, nonhostiles_left

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

        if not self.id:
            return

        character.db.combat_actionsleft = ACTIONS_PER_TURN  # Replenish actions
        character.regenerate(secs=SECS_PER_TURN)

        other_fighters = self.obj.contents
        other_fighters.remove(character)
        if character.db.hostile_to_players:
            msg = "|[100"
        else:
            msg = "|[010"
        msg = msg + ("~~~ %s's Turn ~~~" % (character.name.capitalize()))
        for obj in other_fighters:
            obj.msg(msg)

        # Prompt the character for their turn and give some information.
        character.msg("|[551|=a~~~~~ YOUR TURN ~~~~~~")

        table = evtable.EvTable()
        for fighter in self.db.fighters:
            row = [fighter.get_display_name(capital=True), f"{fighter.db.hp} hp"]
            effects_str = ""
            effects = [script for script in fighter.scripts.all() if inherits_from(script, DurationEffect)]
            for script in effects:
                turns_left = ((script.db.duration - script.db.seconds_passed) // SECS_PER_TURN) - 1
                effects_str = effects_str + f"{script.color()}{script.db.effect_key}|n({turns_left}t)  "

            if effects_str != "":
                row.append(effects_str)
            table.add_row(*row)
        character.msg(table)

        if character.effect_active("Frozen"):
            character.location.msg_contents(character.get_display_name(capital=True) + " is frozen solid and cannot act!")
            self.spend_action(character, "all")
        if character.effect_active("Knocked Down") and character.db.effects["Knocked Down"]["seconds passed"] < 3:
            character.location.msg_contents(
                character.get_display_name() + " loses precious time in battle clambering back to their feet!")
            self.spend_action(character, "all", "stand up")

        character.tick_cooldowns(SECS_PER_TURN)
        character.apply_effects()

        combat_ai = character.db.ai
        if combat_ai:
            delay(2, combat_ai.take_turn)

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

    # TODO: Action Points
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
            try:
                character.db.combat_actionsleft -= actions  # Use up actions.
                if character.db.combat_actionsleft < 0:
                    character.db.combat_actionsleft = 0  # Can't have fewer than 0 actions
            except TypeError:
                return
        character.db.combat_turnhandler.turn_end_check(character)  # Signal potential end of turn.

    def turn_end_check(self, character):
        """
        Tests to see if a character's turn is over, and cycles to the next turn if it is.

        Args:
            character (obj): Character to test for end of turn
        """
        if not character.db.combat_actionsleft:  # Character has no actions remaining
            self.all_defeat_check()
            if not self.id:
                return
            character.cap_stats()
            self.next_turn()
            return

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

        self.all_defeat_check()

        # Cycle to the next turn.
        currentchar = self.db.fighters[self.db.turn]
        while True:
            self.db.turn += 1  # Go to the next in the turn order.
            if self.db.turn > len(self.db.fighters) - 1:
                self.db.turn = 0  # Go back to the first in the turn order once you reach the end.
            newchar = self.db.fighters[self.db.turn]  # Note the new character
            if newchar.db.hp > 0:
                break
        self.db.timer = TURN_TIMEOUT + self.time_until_next_repeat()  # Reset the timer.
        self.db.timeout_warning_given = False  # Reset the timeout warning.

        self.all_defeat_check()

        self.start_turn(newchar)

        if not self.id:
            return

        # Count down condition timers.
        next_fighter = self.db.fighters[self.db.turn]
        """for fighter in self.db.fighters:
            COMBAT.condition_tickdown(fighter, next_fighter)"""

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
        if defeated.db.hp < 0:
            defeated.db.hp = 0

        defeated.at_defeat()

        if defeated.db.hostile_to_players:
            for fighter in self.db.fighters:
                if fighter.attributes.has("xp"):
                    fighter.gain_xp(defeated.get_defeat_xp())

        defeated.location.scripts.get("Combat Turn Handler")[0].all_defeat_check()

        if defeated.is_turn():
            self.spend_action(defeated, actions="all")

        return True

    def all_defeat_check(self):
        """Check if all fighters on one 'side' are defeated - either no hostiles left or no nonhostiles left"""
        if not self.id:
            return
        # Check if all left standing are either hostile or friendly
        hostiles_left, nonhostiles_left = self.count_hostiles()
        if (hostiles_left == 0) or (nonhostiles_left == 0):
            self.obj.msg_contents(f"{appearance.ambient}Quiet falls upon the battlefield.")
            if hostiles_left == 0:
                self.obj.msg_contents("|[350|=aYou are victorious!")
            for fighter in self.db.fighters:
                delay(timedelay=3, callback=fighter.execute_cmd, raw_string="look")
            self.stop()  # Stop this script and end combat.
            self.delete()
            return

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
