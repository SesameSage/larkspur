from evennia.commands.cmdset import CmdSet
from evennia.commands.default.account import CmdIC, CmdOOC
from evennia.commands.default.muxcommand import MuxCommand

from server import appearance


class CmdMainMenu(CmdOOC):
    """
    return to the character selection screen

    Usage:
      mainmenu
      menu
    """
    key = "mainmenu"
    aliases = ("menu",)
    help_category = "account"

class CmdPlay(CmdIC):
    """
    enter the world as the given character

    Usage:
      play <character>

    Take control of a character to play the game.
    """

    key = "play"
    help_category = "account"

class CmdCharCreate(MuxCommand):
    """
    create a new character

    Usage:
      charcreate <charname> [= desc]

    Create a new character, optionally giving it a description. You
    may use upper-case letters in the name - you will nevertheless
    always be able to access your character using lower-case letters.
    """

    key = "charcreate"
    locks = "cmd:pperm(Player)"
    help_category = "General"

    # this is used by the parent
    account_caller = True

    def func(self):
        """create the new character"""
        account = self.account
        if not self.args:
            self.msg("Usage: charcreate <charname> [= description]")
            return
        key = self.lhs
        description = self.rhs or "This is a character."

        new_character, errors = self.account.create_character(
            key=key, description=description, ip=self.session.address
        )

        if errors:
            self.msg(errors)
        if not new_character:
            return

        self.msg(
            f"Created new character {new_character.key}. Use {appearance.cmd}play {new_character.key}|n to enter"
            " the game as this character."
        )

class OOCCmdSet(CmdSet):
    def at_cmdset_creation(self):
        super().at_cmdset_creation()
        self.add(CmdMainMenu())
        self.add(CmdPlay())
        self.add(CmdCharCreate())