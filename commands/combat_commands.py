from evennia import Command, default_cmds
from evennia.commands.default.help import CmdHelp
from evennia.commands.default.muxcommand import MuxCommand

from server import appearance
from turnbattle.turn_handler import TurnHandler
from turnbattle.combat_handler import COMBAT
from typeclasses.inanimate.items.usables import Usable, Consumable
from typeclasses.inanimate.items.weapons import Weapon


class CmdFight(Command):
    """
    start a fight in this location

    Usage:
      fight

    When you start a fight, everyone in the room who is able to
    fight is added to combat, and a turn order is randomly rolled.
    When it's your turn, you can attack other characters.
    """

    key = "fight"
    help_category = "combat"
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
        if self.caller.is_in_combat():  # Already in a fight
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
    attack another entity

    Usage:
      attack <target>

    When in a fight, you may attack another character. The attack has
    a chance to hit, and if successful, will deal damage.
    """

    key = "attack"
    aliases = ["att", "at", "hit"]
    help_category = "combat"

    def func(self):
        if not self.confirm_in_combat():
            return
        if not self.turn_handler.is_turn(self.caller):  # If it's not your turn, can't attack.
            self.caller.msg("You can only do that on your turn.")
            return

        if not self.caller.db.hp:  # Can't attack if you have no HP.
            self.caller.msg("You can't attack, you've been defeated.")
            return

        attacker = self.caller

        valid_targets = []
        for fighter in attacker.location.scripts.get("Combat Turn Handler")[0].db.fighters:
            if fighter is not attacker and fighter.db.hp > 0:
                valid_targets.append(fighter)
        if self.args == "":  # No valid target given.
            if len(valid_targets) > 1:
                self.caller.msg("Attack whom? " + str(valid_targets))
                return
            else:
                defender = valid_targets[0]
        else:
            defender = self.caller.search(self.args, candidates=valid_targets)
            if not defender:
                self.caller.msg("Can't find " + self.args)
                return

        if not defender.db.hp:  # Target object has no HP left or to begin with
            self.caller.msg("You can't fight that!")
            return

        if attacker == defender:  # Target and attacker are the same
            self.caller.msg("You can't attack yourself!")
            return

        COMBAT.resolve_attack(attacker, defender)
        self.turn_handler.spend_action(self.caller, 1, action_name="attack")  # Use up one action.

    def confirm_in_combat(self):
        if not self.caller.is_in_combat():  # If not in combat, can't attack.
            self.caller.msg("You can only do that in combat. (see: help fight)")
            return False

        self.turn_handler = self.caller.db.combat_turnhandler
        return True


class CmdCast(Command):
    """
    cast an ability or spell

    Usage:
      cast <ability/spell>
      cast <ability/spell> <target>

    This attempts to pay the cost and execute one of your abilities or spells by name.
    If a target is required, it must be provided.
    """
    key = "cast"
    aliases = ["cas", "ca", "c"]
    help_category = "combat"

    def func(self):
        # Separate args given after "cast"
        args = self.args.split()
        if len(args) < 1:  # If no args given
            self.caller.msg(f"Usage: {appearance.cmd}cast <ability> |n/ {appearance.cmd}cast <ability> <target>")
            return
        # First arg is ability/spell name
        # TODO: Accommodate giving two word ability names in cast args
        ability_string = args[0].lower()
        try:  # Finding target by name via 2nd arg
            target_string = args[1]
            target = self.caller.search(target_string)
            if not target:
                self.caller.msg("No valid target found for " + target_string)
                return
        except IndexError:  # If no target arg given
            target = None
            # Ability's check function (called with its cast func) will fail if a target is required

        # Find ability/spell by name
        valid_castables = []
        for ability in self.caller.db.abilities:
            if ability.key.lower().startswith(ability_string):
                valid_castables.append(ability)
        if len(valid_castables) == 0:
            self.caller.msg("No valid abilities found for " + ability_string)
            return
        elif len(valid_castables) > 1:
            self.caller.msg("Multiple abilities found for " + ability_string)
            return
        if 0 < len(valid_castables) < 2:
            if valid_castables[0].cast(caster=self.caller, target=target):  # If successfully cast
                # Spend an action if in combat
                if self.caller.is_in_combat():
                    self.caller.db.combat_turnhandler.spend_action(character=self.caller, actions=1, action_name="cast")


class CmdPass(Command):
    """
    pass your turn

    Usage:
      pass

    When in a fight, you can use this command to end your turn early, even
    if there are still any actions you can take.
    """

    key = "pass"
    aliases = ["wait", "hold"]
    help_category = "combat"

    def func(self):
        if not self.confirm_in_combat():
            return

        if not self.turn_handler.is_turn(self.caller):  # Can only pass if it's your turn.
            self.caller.msg("You can only do that on your turn.")
            return

        self.caller.location.msg_contents(
            "%s takes no further action, passing the turn." % self.caller.get_display_name()
        )
        # Spend all remaining actions.
        self.turn_handler.spend_action(self.caller, "all", action_name="pass")

    def confirm_in_combat(self):
        if not self.caller.is_in_combat():  # If not in combat, can't attack.
            self.caller.msg("You can only do that in combat. (see: help fight)")
            return False

        self.turn_handler = self.caller.db.combat_turnhandler
        return True


class CmdDisengage(Command):
    """
    pass turn and attempt to end combat

    Usage:
      disengage

    Ends your turn early and signals that you're trying to end
    the fight. If all participants in a fight disengage, the
    fight ends.
    """

    key = "disengage"
    aliases = ["spare"]
    help_category = "combat"

    def func(self):
        if not self.confirm_in_combat():
            return

        if not self.caller.is_turn():  # If it's not your turn
            self.caller.msg("You can only do that on your turn.")
            return

        self.caller.location.msg_contents("%s disengages, ready to stop fighting." % self.caller)
        # Spend all remaining actions.
        self.turn_handler.spend_action(self.caller, "all", action_name="disengage")
        """
        The action_name kwarg sets the character's last action to "disengage", which is checked by
        the turn handler script to see if all fighters have disengaged.
        """

    def confirm_in_combat(self):
        if not self.caller.is_in_combat():  # If not in combat, can't attack.
            self.caller.msg("You can only do that in combat. (see: help fight)")
            return False

        self.turn_handler = self.caller.db.combat_turnhandler
        return True


class CmdRest(Command):
    """
    recover hp faster

    Usage:
      rest

    Resting recovers your HP to its maximum, but you can only
    rest if you're not in a fight.
    """

    key = "rest"
    help_category = "combat"

    def func(self):
        if self.caller.is_in_combat():  # If you're in combat
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
        if self.caller.is_in_combat() and not self.args:
            self.caller.msg(self.combat_help_text)
        else:
            super().func()  # Call the default help command


class CmdUse(MuxCommand):
    """
    use a usable item

    Usage:
      use <item> [= target]

    An item can have various function - looking at the item may
    provide information as to its effects. Some items can be used
    to attack others, and as such can only be used in combat.
    """

    key = "use"
    help_category = "items"

    def func(self):
        """
        This performs the actual command.
        """
        # TODO: Remove = requirement as done in cast command
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
        if self.caller.is_in_combat():
            if not self.caller.is_turn():
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
        COMBAT.use_item(self.caller, item, target)


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
        self.add(CmdCast())
        self.add(CmdRest())
        self.add(CmdPass())
        self.add(CmdDisengage())
        self.add(CmdCombatHelp())
        self.add(CmdUse())
