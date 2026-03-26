from evennia.commands.cmdset import CmdSet
from evennia.commands.default.account import CmdIC


class CmdPlay(CmdIC):
    """
    enter the world as the given character

    Usage:
      playas <character>

    Take control of a character to play the game.
    """

    key = "play"
    help_category = "account"

class OOCCmdSet(CmdSet):
    def at_cmdset_creation(self):
        super().at_cmdset_creation()
        self.add(CmdPlay())