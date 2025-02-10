from evennia import Command, default_cmds
from evennia.commands.default.help import CmdHelp
from evennia.commands.default.muxcommand import MuxCommand

from turnbattle.turn_handler import TurnHandler
from turnbattle.rules import COMBAT_RULES
from typeclasses.inanimate.items.usables import Usable, Consumable


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
        # Search for item in caller's inv
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

        if not isinstance(item, Usable):  # Object has no item_func, not usable
            self.caller.msg("'%s' is not a usable item." % item.key.capitalize())
            return

        if isinstance(item, Consumable):  # Item has limited uses
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
        self.add(CmdUse())
        self.add(CmdWield())
