from evennia.commands.cmdset import CmdSet
from evennia.commands.default.muxcommand import MuxCommand
from evennia.utils import inherits_from

from server import appearance


# TODO: PM/whisper from anywhere

class CmdTalk(MuxCommand):
    """
    Talks to an npc

    Usage:
      talk

    This command is only available if a talkative non-player-character
    (NPC) is actually present. It will strike up a conversation with
    that NPC and give you options on what to talk about.
    """

    key = "talk"
    locks = "cmd:all()"
    help_category = "communication"

    def func(self):
        npc_input = self.lhs
        if not npc_input:
            self.caller.msg("Talk to whom?")
            return
        npc = self.caller.search(npc_input)
        if not npc:
            return
        if not inherits_from(npc, "typeclasses.living.characters.Character"):
            self.caller.msg(npc.key + " is not a character you can talk to!")
            return
        npc.at_talk(self.caller)


class CmdTell(MuxCommand):
    key = "tell"
    help_category = "communication"

    def func(self):
        receiver_input = self.lhs
        receiver = self.caller.search(receiver_input)
        if not receiver:
            self.caller.msg(f"No one found here for '{receiver_input}'")
            return

        msg = self.rhs

        self.caller.at_say(message=msg, msg_self=True, msg_location=f"{self.caller.color()}$You()|n $conj(tell) "
                                                                    f"{receiver.get_display_name()}: {appearance.say}"
                                                                    + "{speech}")
        self.caller.at_tell(receiver, msg)
        receiver.at_told(self.caller, msg)


class CommsCmdSet(CmdSet):
    def at_cmdset_creation(self):
        self.add(CmdTalk)
        self.add(CmdTell)
