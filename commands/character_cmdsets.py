from evennia import Command
from evennia.contrib.grid.ingame_map_display import MapDisplayCmdSet

from commands.permissions_cmdsets import BuildingCmdSet
from commands.refiled_cmds import *
from typeclasses.inanimate.items.containers import ContainerCmdSet
from typeclasses.inanimate.items.items import CmdIdentify, CmdBuy, CmdShop
from typeclasses.inanimate.portals import CmdTravel
from typeclasses.living.char_stats import StatsCmdSet
from typeclasses.living.talking_npc import TalkingCmdSet


class CmdMoreInfo(Command):
    key = "moreinfo"
    help_category = "appearance"

    def func(self):
        self.caller.attributes.get("prefs", category="ooc")["more_info"] = \
            not self.caller.attributes.get("prefs", category="ooc")["more_info"]
        self.caller.print_ambient(
            f"MoreInfo set to {self.caller.attributes.get("prefs", category="ooc")["more_info"]}.")


class PlayerCmdSet(CmdSet):
    key = "DefaultCharacter"

    def at_cmdset_creation(self):
        super().at_cmdset_creation()
        self.add(MapDisplayCmdSet)
        self.add(BuildingCmdSet)
        self.add(TalkingCmdSet)
        self.add(ContainerCmdSet)
        self.add(StatsCmdSet)

        self.add(CmdMoreInfo)
        self.add(CmdTravel)
        self.add(CmdIdentify)
        self.add(CmdBuy)
        self.add(CmdShop)
