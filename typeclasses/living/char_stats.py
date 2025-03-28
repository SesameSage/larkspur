from enum import Enum

from evennia import Command, CmdSet


class CharAttrib(Enum):
    STRENGTH = 1
    CONSTITUTION = 2
    DEXTERITY = 3
    PERCEPTION = 4
    INTELLIGENCE = 5
    WISDOM = 6
    SPIRIT = 7

    def get_display_name(self):
        return self.name.lower().capitalize()

    def get_short_name(self):
        return self.name[:3]


class CmdHP(Command):
    key = "hp"
    help_category = "character"

    def func(self):
        if self.args:
            target = self.caller.search(self.args)
            if not target:
                self.caller.msg(f"Can't find '{self.args}' here")
                return
            if not target.db.hp:
                self.caller.msg(f"{target.name} doesn't have hitpoints!")
                return
            self.caller.msg(f"{target.name} HP: {target.db.hp}")
        else:
            self.caller.msg(f"Your HP: {self.caller.db.hp}")


class CmdMana(Command):
    key = "mana"
    aliases = "man"
    help_category = "character"

    def func(self):
        if self.args:
            target = self.caller.search(self.args)
            if not target:
                self.caller.msg(f"Can't find '{self.args}' here")
                return
            if not target.db.mana:
                self.caller.msg(f"{target.name} doesn't have mana!")
                return
            self.caller.msg(f"{target.name} mana: {target.db.mana}")
        else:
            self.caller.msg(f"Your mana: {self.caller.db.mana}")


class CmdStamina(Command):
    key = "stamina"
    aliases = "stam"
    help_category = "character"

    def func(self):
        if self.args:
            target = self.caller.search(self.args)
            if not target:
                self.caller.msg(f"Can't find '{self.args}' here")
                return
            if not target.db.stamina:
                self.caller.msg(f"{target.name} doesn't have stamina!")
                return
            self.caller.msg(f"{target.name} stamina: {target.db.stamina}")
        else:
            self.caller.msg(f"Your stamina: {self.caller.db.stamina}")

class StatsCmdSet(CmdSet):
    key = "PlayerCharacter"
    def at_cmdset_creation(self):
        super().at_cmdset_creation()
        self.add(CmdHP)
        self.add(CmdMana)
        self.add(CmdStamina)
