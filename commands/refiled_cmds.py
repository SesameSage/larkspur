"""These commands have only had their category in the help table changed from default Evennia commands."""

from evennia import CmdSet
from evennia.commands.default.account import CmdColorTest, CmdQuit, CmdSessions, CmdStyle, CmdWho, CmdPassword, CmdIC, \
    CmdOOC, CmdOption
from evennia.commands.default.comms import CmdChannel, CmdPage
from evennia.commands.default.general import CmdSay, CmdWhisper, CmdDrop, CmdGive, CmdNick, CmdPose, \
    CmdAccess, CmdSetDesc
from evennia.contrib.game_systems.containers.containers import CmdPut
from evennia.contrib.grid.simpledoor.simpledoor import CmdOpenCloseDoor

from world.ingame_map_display import CmdMap


class MyCmdSay(CmdSay):
    help_category = "communication"


class MyCmdWhisper(CmdWhisper):
    help_category = "communication"


class MyCmdChannel(CmdChannel):
    help_category = "communication"


class MyCmdPage(CmdPage):
    help_category = "communication"
    aliases = ()


class MyCmdMap(CmdMap):
    help_category = "navigation"


class MyCmdDrop(CmdDrop):
    help_category = "items"


class MyCmdGive(CmdGive):
    help_category = "items"


class MyCmdPut(CmdPut):
    help_category = "items"


class MyCmdNick(CmdNick):
    help_category = "appearance"


class MyCmdPose(CmdPose):
    locks = "cmd:false()"


class MyCmdAccess(CmdAccess):
    help_category = "account"


class MyCmdSetDesc(CmdSetDesc):
    help_category = "character"


class RefiledCmdSet(CmdSet):
    key = "PlayerCharacter"

    def at_cmdset_creation(self):
        super().at_cmdset_creation()
        self.add(MyCmdSay)
        self.add(MyCmdWhisper)
        self.add(MyCmdChannel)
        self.add(MyCmdPage)
        self.add(MyCmdDrop)
        self.add(MyCmdGive)
        self.add(MyCmdPut)
        self.add(MyCmdNick)
        self.add(MyCmdPose)
        self.add(MyCmdMap)
        self.add(MyCmdAccess)
        self.add(MyCmdSetDesc)
        self.add(MyCmdOpenDoor)


class MyCmdColor(CmdColorTest):
    help_category = "appearance"


class MyCmdQuit(CmdQuit):
    help_category = "system"


class MyCmdSessions(CmdSessions):
    help_category = "system"


class MyCmdStyle(CmdStyle):
    help_category = "appearance"


class MyCmdWho(CmdWho):
    help_category = "communication"


class MyCmdPassword(CmdPassword):
    help_category = "account"


class MyCmdIC(CmdIC):
    help_category = "account"


class MyCmdOOC(CmdOOC):
    help_category = "account"


class MyCmdOption(CmdOption):
    help_category = "account"


class MyCmdOpenDoor(CmdOpenCloseDoor):
    help_category = "navigation"
