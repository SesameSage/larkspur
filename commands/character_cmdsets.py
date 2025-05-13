from commands.info_commands import CmdMoreInfo, CmdHere, MyCmdHelp
from commands.permissions_cmdsets import BuildingCmdSet
from commands.refiled_cmds import *
from commands.stats_commands import CmdClasses, CmdLearn, CmdSpells, StatsCmdSet
from typeclasses.inanimate.items.containers import ContainerCmdSet
from typeclasses.inanimate.items.items import CmdIdentify, CmdBuy, CmdShop
from typeclasses.inanimate.portals import CmdTravel
from typeclasses.living.talking_npc import TalkingCmdSet


class PlayerCmdSet(CmdSet):
    key = "DefaultCharacter"

    def at_cmdset_creation(self):
        super().at_cmdset_creation()
        self.add(BuildingCmdSet)
        self.add(TalkingCmdSet)
        self.add(ContainerCmdSet)
        self.add(StatsCmdSet)

        self.add(MyCmdHelp)
        self.add(CmdMoreInfo)
        self.add(CmdHere)
        self.add(CmdClasses)
        self.add(CmdLearn)
        self.add(CmdSpells)

        self.add(CmdTravel)
        self.add(CmdIdentify)
        self.add(CmdBuy)
        self.add(CmdShop)
