# TODO: Update TurnHandler docs
from random import randint

import evennia
from evennia.utils import evtable, inherits_from, delay
from evennia.utils.create import create_script

from combat.combat_grid import CombatGrid
from combat.combat_handler import COMBAT
from server import appearance
from combat.effects import DurationEffect
from combat.combat_constants import SECS_PER_TURN
from typeclasses.inanimate.items.equipment.weapons import Weapon
from typeclasses.scripts.scripts import Script

TURN_TIMEOUT = 30  # Time before turns automatically end, in seconds


def start_join_fight(attacker, target, action):
    """Start a fight if not already started, and/or add attacker and target to the fight if not already participating."""
    # Don't start a fight if the move wasn't offensive or target wasn't an enemy
    if not target:
        return
    if not isinstance(action, str) and action.attributes.has("cooldown"):
        if not action.db.offensive:
            return
    if not isinstance(target, tuple) and attacker.db.hostile_to_players == target.db.hostile_to_players:
        return

    here = attacker.location
    if not attacker.is_in_combat():
        if here.db.combat_turnhandler:
            here.db.combat_turnhandler.join_fight(attacker)
        else:
            rng = COMBAT.action_range(action)
            create_script(typeclass=TurnHandler, obj=here,
                          attributes=[("starter", attacker), ("start_target", target),
                                      ("starter_distance", rng if rng < 8 else 8)])
    if not isinstance(target, tuple) and not target.is_in_combat():
        if here.db.combat_turnhandler:
            here.db.combat_turnhandler.join_fight(target)


class TurnHandler(Script):
    """
    This is the script that handles the progression of combat through turns.
    On creation (when a fight is started) it adds all combat-ready characters
    to its roster and then sorts them into a turn order. There can only be one
    fight going on in a single room at a time, so the script is assigned to a
    room as its object.

    Fights persist until only one participant is left with any HP or all
    remaining participants choose to end the combat with the 'disengage' command.
    """

    # <editor-fold desc="Script methods">
    def at_script_creation(self):
        """
        Called once, when the script is created.
        """
        super().at_script_creation()
        self.key = "Combat Turn Handler"
        self.interval = 5  # Once every 5 seconds
        self.persistent = True
        self.db.grid = None
        self.db.fighters = []

        self.db.round = 0

        self.db.starter = None
        self.db.start_target = None
        self.db.starter_distance = None

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
        self.db.turn_order_pos = 0
        self.db.timer = TURN_TIMEOUT  # Set timer to turn timeout specified in options

    def at_start(self, **kwargs):
        """Turn order and battlefield position must be generated after at_script_creation so that self.db.starter is
        available to access.
        This is also called on a server restart, so calls after the first round has begun are ignored, or it would
        always become the fight starter's turn at reload, and positions would always reset."""
        # Skip calls on server reload - only call after initialization
        if not self.db.round == 0:
            return

        self.roll_turn_order()

        # Push the fight starter to the beginning
        self.db.fighters.remove(self.db.starter)
        self.db.fighters.insert(0, self.db.starter)

        self.db.grid = create_script(typeclass=CombatGrid, obj=self.obj, attributes=[("objects", self.db.fighters)])

        # Start first fighter's turn.
        self.db.round = 1
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
        try:
            self.db.grid.stop()
            self.db.grid.delete()
        except AttributeError:
            pass

    def at_repeat(self):
        """
        Called once every self.interval seconds.
        """
        currentchar = self.db.fighters[
            self.db.turn_order_pos
        ]  # Note the current character in the turn order.
        self.db.timer -= self.interval  # Count down the timer.
        """self.all_defeat_check()"""

        if self.db.timer <= 0:
            # Force current character to disengage if timer runs out.
            self.obj.msg_contents("%s's turn timed out!" % currentchar.get_display_name(capital=True))
            self.next_turn()
            return
        elif self.db.timer <= 10 and not self.db.timeout_warning_given:  # 10 seconds left
            # Warn the current character if they're about to time out.
            currentchar.msg(f"{appearance.warning}WARNING: About to time out!")
            self.db.timeout_warning_given = True

    # </editor-fold>

    def initialize_for_combat(self, character):
        """
        Prepares a character for combat when starting or entering a fight.

        Args:
            character (obj): Character to initialize for combat.
        """
        # Clean up leftover combat attributes beforehand, just in case.
        self.combat_cleanup(character)
        character.db.combat_ap = (
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
        self.db.fighters.insert(self.db.turn_order_pos, character)
        # Tick the turn counter forward one to compensate.
        self.db.turn_order_pos += 1
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

        character.regenerate(SECS_PER_TURN)
        gain_ap = True
        if (character.effect_active("Frozen")
                or character.effect_active("Knocked Down") and character.db.effects["Knocked Down"][
                    "seconds passed"] < 3):
            gain_ap = False
        if gain_ap:
            character.db.combat_ap += COMBAT.get_ap(character)  # Replenish actions

        # Set AP to spend on the first step, then let entity take steps up to speed before spending more
        character.db.combat_stepsleft = 1

        # Display grid
        for content in self.obj.contents:
            content.msg(self.db.grid.print())

        # Show turn to other players
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

        table = evtable.EvTable(pretty_corners=True)
        for fighter in self.db.fighters:
            row = [f"|=l({fighter.db.combat_x},{fighter.db.combat_y})|n " + fighter.get_display_name(capital=True),
                   f"{appearance.hp}{fighter.db.hp} "
                   f"{appearance.stamina}{fighter.db.stamina} "
                   f"{appearance.mana}{fighter.db.mana}"]
            effects_str = ""
            effects = [script for script in fighter.scripts.all() if inherits_from(script, DurationEffect)]
            for script in effects:
                turns_left = ((script.db.duration - script.db.seconds_passed) // SECS_PER_TURN)
                turns_left -= 1 if script.obj != character else 0
                effects_str = effects_str + f"{script.color()}{script.db.effect_key}|n({turns_left}t)  "

            if effects_str != "":
                row.append(effects_str)
            table.add_row(*row)
        character.msg(table)
        character.msg(f"You have {appearance.highlight}{character.db.combat_ap} AP.")

        # Cycle their cooldowns and effects
        character.tick_cooldowns(SECS_PER_TURN)
        character.apply_effects()

        # Apply turn effects
        if character.effect_active("Frozen"):
            character.location.msg_contents(
                character.get_display_name(capital=True) + " is frozen solid and cannot act!")
            # Turn will already be skipped if AP was 0 because none was gained
            if character.db.combat_ap > 0:
                self.next_turn()

        if character.effect_active("Knocked Down") and character.db.effects["Knocked Down"]["seconds passed"] <= 3:
            character.location.msg_contents(
                character.get_display_name(
                    capital=True) + " loses precious time in battle clambering back to their feet!")
            # Turn will already be skipped if AP was 0 because none was gained
            if character.db.combat_ap > 0:
                self.next_turn()

        # Take turn if AI
        combat_ai = character.db.ai
        if combat_ai:
            combat_ai.take_turn()

    def is_turn(self, character):
        """
        Returns true if it's currently the given character's turn in combat.

        Args:
            character (obj): Character to determine if it is their turn or not

        Returns:
            (bool): True if it is their turn or False otherwise
        """
        turnhandler = character.db.combat_turnhandler
        currentchar = turnhandler.db.fighters[turnhandler.db.turn_order_pos]
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
            character.db.combat_ap = 0  # Set actions to 0
        else:
            try:
                character.db.combat_ap -= actions  # Use up actions.
                if character.db.combat_ap < 0:
                    character.db.combat_ap = 0  # Can't have fewer than 0 actions
            except TypeError:
                # This must return instead of pass so that AP isn't printed twice when an action is commanded before
                # combat begins
                return
        self.turn_end_check(character)  # Signal potential end of turn.

    def turn_end_check(self, character):
        """
        Tests to see if a character's turn is over, and cycles to the next turn if it is.

        Args:
            character (obj): Character to test for end of turn
        """
        if character.db.combat_ap > 0:
            character.msg(f"You have {appearance.highlight}{character.db.combat_ap} AP.")
        else:  # Character has no actions remaining
            if not self.id:
                return
            character.cap_stats()
            self.next_turn()
            return

    def next_turn(self):
        """
        Advances to the next character in the turn order.
        """
        self.all_defeat_check()

        # Cycle to the next turn.
        currentchar = self.db.fighters[self.db.turn_order_pos]
        while True:
            self.db.turn_order_pos += 1  # Go to the next in the turn order.
            if self.db.turn_order_pos > len(self.db.fighters) - 1:
                self.db.turn_order_pos = 0  # Go back to the first in the turn order once you reach the end.
                self.db.round += 1
            newchar = self.db.fighters[self.db.turn_order_pos]  # Note the new character
            if newchar.db.hp > 0:
                break
        self.db.timer = TURN_TIMEOUT + self.time_until_next_repeat()  # Reset the timer.
        self.db.timeout_warning_given = False  # Reset the timeout warning.

        self.start_turn(newchar)

        if not self.id:
            return

        # Count down condition timers.
        next_fighter = self.db.fighters[self.db.turn_order_pos]
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
