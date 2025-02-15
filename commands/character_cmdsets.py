from evennia import CmdSet, Command


class CmdMoreInfo(Command):
    key = "moreinfo"

    def func(self):
        self.caller.attributes.get("prefs")["more_info"] = not self.caller.attributes.get("prefs")["more_info"]
        self.caller.print_ambient(f"MoreInfo set to {self.caller.attributes.get("prefs")["more_info"]}.")


class PrefsCmdSet(CmdSet):
    key = "DefaultCharacter"

    def at_cmdset_creation(self):
        super().at_cmdset_creation()
        self.add(CmdMoreInfo)
