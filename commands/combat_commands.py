from evennia import Command, default_cmds
from evennia.commands.default.help import CmdHelp
from evennia.commands.default.muxcommand import MuxCommand
from evennia.utils.create import create_script

from combat.combat_handler import COMBAT
from combat.turn_handler import TurnHandler, start_join_fight
from server import appearance
from typeclasses.inanimate.items.usables import Usable, Consumable


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
        attacker = self.caller
        if attacker.effect_active("Ceasefire"):
            attacker.msg("Can't attack during a ceasefire!")
            return

        visible_things = attacker.filter_visible(attacker.location.contents, attacker)
        valid_targets = [content for content in visible_things
                         if content.db.hp and content.db.hostile_to_players != attacker.db.hostile_to_players]

        # With no args, display list unless there is only one valid target
        if self.args == "":
            if len(valid_targets) > 1:
                attacker.msg("Attack whom? " + str(valid_targets))
                return
            else:
                target = valid_targets[0]
        else:
            target = attacker.search(self.args, candidates=valid_targets)
            if not target:
                attacker.msg("Can't find " + self.args)
                return

        start_join_fight(attacker, target, attacker.get_weapon())

        # Wait to check this until after start_join_fight to make sure combat_ap is accessible
        if attacker.db.combat_ap < attacker.ap_to_attack():
            attacker.msg("Not enough AP!")
            return
        tile_effects = [
            eff.db.effect_key for eff in
            self.caller.db.combat_turnhandler.db.grid.effects_at(self.caller.db.combat_x, self.caller.db.combat_y)
        ]
        if "Swarm" in tile_effects:
            self.caller.msg("Insects swarm around your face, preventing you from attacking!")
            return

        attacker.attack(target)


class CmdCast(MuxCommand):
    """
    cast an ability or spell

    Usage:
      cast <ability/spell>
      cast <ability/spell> <target>

    This attempts to pay the cost and execute one of your abilities or spells by name.
    If a target is required, it must be provided.
    """
    key = "cast"
    rhs_split = ("=", " on ", " at ")
    aliases = ["cas", "ca", "c"]
    help_category = "combat"

    def func(self):
        # Left is ability/spell name
        if not self.lhs:
            self.caller.msg(
                f"Cast what? {appearance.cmd}cast <ability>|n or {appearance.cmd}cast <ability> on <target>")
            return
        ability_string = self.lhs

        # Right (if present) is target
        if not self.rhs:
            # Ability's check function (called with its cast func) will fail if a target is required
            target = None
        else:
            target_string = self.rhs
            if target_string == "me":
                target = self.caller
            else:
                # Attempt to parse a grid coordinate
                x = None
                y = None
                try:
                    x, y = target_string.split(",")
                    x = int(x)
                    y = int(y)
                except ValueError:
                    pass

                # Search for object target otherwise
                if x is None or y is None:
                    target = self.caller.search(target_string, candidates=[
                    content for content in self.caller.location.contents if content.attributes.has("hp")])
                else:
                    target = (x, y)
            if not target:
                self.caller.msg("No valid target found for " + target_string)
                return

        # Find ability/spell by name
        valid_castables = []
        for ability in self.caller.db.abilities:
            if ability.key.lower().startswith(ability_string.lower()):
                valid_castables.append(ability)
        if len(valid_castables) == 0:
            self.caller.msg("No valid abilities found for " + ability_string)
            return
        elif len(valid_castables) > 1:
            self.caller.msg("Multiple abilities found for " + ability_string)
            return

        if 0 < len(valid_castables) < 2:
            ability = valid_castables[0]

            # If offensive, start/join a fight if applicable and not already in one
            if ability.db.offensive:
                start_join_fight(self.caller, target, ability)

            ability.cast(caster=self.caller, target=target)


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
    rhs_split = ("=", " on ")
    help_category = "items"

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


# <editor-fold desc="Directions">
# A combination of these commands and the at_pre_move override is necessary to get the combat version of the movement
# commands to execute whether there is a valid room exit found or not.
class DirCmd(MuxCommand):
    help_category = ""

    def func(self):
        if not self.caller.is_in_combat():
            found_exit = False
            for ext in self.caller.location.exits:
                if self.key == ext.key:
                    self.caller.move_to(destination=ext, move_type="traverse")
                    found_exit = True
            if not found_exit:
                self.caller.msg("You can't go that way.")
        else:
            self.caller.db.combat_turnhandler.db.grid.step(self.caller, self.aliases[0])


class CmdNorth(DirCmd):
    key = "north"
    aliases = ["n"]


class CmdSouth(DirCmd):
    key = "south"
    aliases = ["s"]

class CmdEast(DirCmd):
    key = "east"
    aliases = ["e"]


class CmdWest(DirCmd):
    key = "west"
    aliases = ["w"]


class CmdNorthwest(DirCmd):
    key = "northwest"
    aliases = ["nw"]


class CmdNortheast(DirCmd):
    key = "northeast"
    aliases = ["ne"]


class CmdSouthwest(DirCmd):
    key = "southwest"
    aliases = ["sw"]


class CmdSoutheast(DirCmd):
    key = "southeast"
    aliases = ["se"]
# </editor-fold>


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

        self.caller.location.msg_contents(f"{self.caller.get_display_name(capital=True)} passes the turn.")
        self.caller.db.combat_lastaction = "pass"
        self.turn_handler.next_turn()

    def confirm_in_combat(self):
        if not self.caller.is_in_combat():  # If not in combat, can't attack.
            self.caller.msg("You can only do that in combat. (see: help fight)")
            return False

        self.turn_handler = self.caller.db.combat_turnhandler
        return True


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


class BattleCmdSet(default_cmds.CharacterCmdSet):
    """
    This command set includes all the commmands used in the battle system.
    """

    key = "DefaultCharacter"

    def at_cmdset_creation(self):
        """
        Populates the cmdset
        """
        self.add(CmdAttack())
        self.add(CmdCast())
        self.add(CmdPass())
        self.add(CmdCombatHelp())
        self.add(CmdUse())

        self.add(CmdNorth)
        self.add(CmdSouth)
        self.add(CmdEast)
        self.add(CmdWest)
        self.add(CmdNortheast)
        self.add(CmdNorthwest)
        self.add(CmdSoutheast)
        self.add(CmdSouthwest)
