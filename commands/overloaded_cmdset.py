from evennia.commands.cmdset import CmdSet

from commands.all_player_cmds.info_cmds import MyCmdHelp
from commands.perm_cmds.building_cmds import MyCmdDig, MyCmdTunnel


class OverloadedCmdSet(CmdSet):
    def at_cmdset_creation(self):
        self.add(MyCmdHelp)
        self.add(MyCmdDig)
        self.add(MyCmdTunnel)