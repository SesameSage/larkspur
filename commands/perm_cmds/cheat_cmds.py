from evennia.commands.cmdset import CmdSet
from evennia.commands.default.muxcommand import MuxCommand


class CmdEndCombat(MuxCommand):
    """
    end combat in the current room

    Usage:
      endcombat
    """
    key = "endcombat"
    locks = "cmd:perm(Builder) or perm(endcombat)"
    help_category = "combat"

    def func(self):
        room = self.caller.location
        for script in room.scripts.all():
            if script.attributes.has("round"):
                script.delete()
                break

class CheatCmdSet(CmdSet):
    def at_cmdset_creation(self):
        super().at_cmdset_creation()
        self.add(CmdEndCombat)