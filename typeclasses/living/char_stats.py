from enum import Enum

from evennia import Command, CmdSet, EvTable


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
                self.caller.msg(f"{target.name.capitalize()} doesn't have hitpoints!")
                return
            self.caller.msg(f"{target.name.capitalize()} HP: {target.db.hp}")
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
                self.caller.msg(f"{target.name.capitalize()} doesn't have mana!")
                return
            self.caller.msg(f"{target.name.capitalize()} mana: {target.db.mana}")
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
                self.caller.msg(f"{target.name.capitalize()} doesn't have stamina!")
                return
            self.caller.msg(f"{target.name.capitalize()} stamina: {target.db.stamina}")
        else:
            self.caller.msg(f"Your stamina: {self.caller.db.stamina}")


class CmdStats(Command):
    key = "stats"
    help_category = "character"

    def func(self):
        if self.args:
            target = self.caller.search(self.args)
            if not target:
                self.caller.msg(f"Can't find '{self.args}' here")
                return
            if not target.db.hp:
                self.caller.msg(f"{target.name.capitalize()} doesn't have relevant stats!")
                return
        else:
            target = self.caller

        table = EvTable()
        table.add_column(f"Level:\n"
                         f"HP:\n"
                         f"Mana:\n"
                         f"Stamina:\n\n"
                         f"Defense:\n"
                         f"Evasion:\n"
                         f"Resistance:", header=f"{target.get_display_name()}")
        table.add_column(f"{target.db.level}\n"
                         f"|500{target.db.hp}/{target.db.max_hp}|n\n"
                         f"|125{target.db.mana}/{target.db.max_mana}|n\n"
                         f"|030{target.db.stamina}/{target.db.max_stam}|n\n\n"
                         f"{target.get_defense()} ({target.db.char_defense})\n"
                         f"{target.get_evasion()} ({target.db.char_evasion})\n"
                         f"{target.get_resistance()} ({target.db.char_resistance})"
                         )
        table.add_column(f"Strength:\n"
                         f"Constitution:\n"
                         f"Dexterity:\n"
                         f"Perception:\n"
                         f"Intelligence:\n"
                         f"Wisdom:\n"
                         f"Spirit:")
        table.add_column(f"{target.get_attr("str")} ({target.db.attribs["strength"]})\n"
                         f"{target.get_attr("con")} ({target.db.attribs["constitution"]})\n"
                         f"{target.get_attr("dex")} ({target.db.attribs["dexterity"]})\n"
                         f"{target.get_attr("per")} ({target.db.attribs["perception"]})\n"
                         f"{target.get_attr("int")} ({target.db.attribs["intelligence"]})\n"
                         f"{target.get_attr("wis")} ({target.db.attribs["wisdom"]})\n"
                         f"{target.get_attr("spi")} ({target.db.attribs["spirit"]})")
        self.caller.msg(table)


class StatsCmdSet(CmdSet):
    key = "PlayerCharacter"

    def at_cmdset_creation(self):
        super().at_cmdset_creation()
        self.add(CmdHP)
        self.add(CmdMana)
        self.add(CmdStamina)
        self.add(CmdStats)
