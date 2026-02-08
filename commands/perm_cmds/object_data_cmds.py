from evennia.commands.cmdset import CmdSet
from evennia.commands.default.muxcommand import MuxCommand

from server import appearance


class CmdAppear(MuxCommand):
    """
            change how an entity appears in the room

            Usage:
              appear <character> = <string>

            Example:
            appear wolf = snarls.

            This allows for changing how an entity appears when looking at the room
            it's in. The subject of the sentence will be added at the beginning
            automatically, so only the action/appearance must be set.
            """
    key = "appear"
    locks = "cmd:perm(appear) or perm(Builder)"
    help_category = "building"

    def func(self):
        if not self.lhs or not self.rhs:
            self.caller.msg(f"Usage: {appearance.cmd}appear <character> = <string>")
            return
        character_input = self.lhs
        string_input = self.rhs

        # Find character
        character = None
        for obj in self.caller.location.contents:
            if obj.name.lower().startswith(character_input.lower()):
                character = obj
                break
        if not character:
            self.caller.msg("No character here found for " + character_input)
            return

        character.db.appear_string = f"{character.get_display_name(article=True, capital=True)} {string_input}"
        self.caller.msg(character.db.appear_string)


class ObjectDataCmdSet(CmdSet):
    def at_cmdset_creation(self):
        self.add(CmdAppear)
