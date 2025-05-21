from evennia.commands.cmdset import CmdSet
from evennia.commands.default.muxcommand import MuxCommand

from server import appearance


# TODO: PM/whisper from anywhere

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
        self.add(CmdTell)
