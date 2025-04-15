from enum import Enum

from evennia import Command, CmdSet, EvTable

from combat.effects import DamageTypes
from server import appearance


class CmdHP(Command):
    """
        show current hitpoints

        Usage:
          hp (my hp)
          hp <entity>

        Get a combat entity's current hitpoints.
        Hitpoints are analogous to health or life. You are defeated when your hp falls to zero.
        """
    key = "hp"
    help_category = "character"

    def func(self):
        if self.args:  # Target given
            target = self.caller.search(
                self.args, candidates=[content for content in self.caller.location.contents if content.db.hp])
            if not target:
                self.caller.msg(f"Can't find '{self.args}' here")
                return
            if not target.db.hp:
                self.caller.msg(f"{target.name.capitalize()} doesn't have hitpoints!")
                return
            self.caller.msg(f"{target.name.capitalize()} HP: {target.db.hp}")
        else:  # Show self HP
            self.caller.msg(f"Your HP: {self.caller.db.hp}")


class CmdMana(Command):
    """
        show current mana

        Usage:
          mana (my stamina)
          mana <entity>

        Get a combat entity's current mana.
        Mana is a resource used to cast spells."""
    key = "mana"
    aliases = "man"
    help_category = "character"

    def func(self):
        if self.args:  # Target given
            target = self.caller.search(
                self.args, candidates=[content for content in self.caller.location.contents if content.db.mana])
            if not target:
                self.caller.msg(f"Can't find '{self.args}' here")
                return
            if not target.db.mana:
                self.caller.msg(f"{target.name.capitalize()} doesn't have mana!")
                return
            self.caller.msg(f"{target.name.capitalize()} mana: {target.db.mana}")
        else:  # Show self mana
            self.caller.msg(f"Your mana: {self.caller.db.mana}")


class CmdStamina(Command):
    """
    show current stamina

    Usage:
      stamina (my stamina)
      stamina <entity>

    Get a combat entity's current stamina.
    Stamina is a resource used for physical abilities such as Sweep and Shield Bash.
    """
    key = "stamina"
    aliases = "stam"
    help_category = "character"

    def func(self):
        if self.args:  # Target given
            target = self.caller.search(
                self.args, candidates=[content for content in self.caller.location.contents if content.db.stamina])
            if not target:
                self.caller.msg(f"Can't find '{self.args}' here")
                return
            if not target.db.stamina:
                self.caller.msg(f"{target.name.capitalize()} doesn't have stamina!")
                return
            self.caller.msg(f"{target.name.capitalize()} stamina: {target.db.stamina}")
        else:  # Show self stamina
            self.caller.msg(f"Your stamina: {self.caller.db.stamina}")


class CmdStats(Command):
    """
    show a combat entity's stats

    Usage:
      stats (your stats)
      stats <entity>

    Prints a table showing a combat entity's stats, such as hitpoints and strength.

    Values such as resistance and constitution display the active value first, taking
    equipment and effects into account, then display the base character value in parentheses.
    """
    key = "stats"
    aliases = "stat"
    help_category = "character"

    def func(self):

        def display_resistances(target):
            string = ""

            # Display base character defense, evasion, and resistance
            stat_mapping = {target.get_defense: target.db.char_defense[None],
                         target.get_evasion: target.db.char_evasion,
                         target.get_resistance: target.db.char_resistance[None]}
            for stat_func in stat_mapping:
                string = string + f"{appearance.highlight}{stat_func(quiet=True)}|n "
                try:
                    char_stat = stat_mapping[stat_func]
                except KeyError:
                    char_stat = 0
                string = string + f"({char_stat})\n"

            # Add separation and extra line to align with "Resists:" subheader
            string = string + "\n\n"

            # Display specific resistances
            for damage_type in DamageTypes:

                if damage_type in [DamageTypes.BLUNT, DamageTypes.SLASHING, DamageTypes.PIERCING]:
                    stat = target.db.char_defense
                    stat_method = target.get_defense
                elif damage_type in [DamageTypes.FIRE, DamageTypes.COLD, DamageTypes.SHOCK, DamageTypes.POISON]:
                    stat = target.db.char_resistance
                    stat_method = target.get_resistance

                string = string + f"{appearance.highlight}{stat_method(damage_type, type_only=True, quiet=True)}|n "
                try:
                    char_stat = stat[damage_type]
                except KeyError:
                    char_stat = 0
                string = string + f"({char_stat})\n"

            return string

        if self.args:  # Target given
            target = self.caller.search(
                self.args, candidates=[content for content in self.caller.location.contents if content.db.hp])
            if not target:
                self.caller.msg(f"Can't find '{self.args}' here")
                return
            if not target.db.hp:
                self.caller.msg(f"{target.name.capitalize()} doesn't have relevant stats!")
                return
        else:  # Show self stats
            target = self.caller

        table = EvTable()
        table.add_column(f"Class:\n"
                         f"Level:\n"
                         f"HP:\n"
                         f"Mana:\n"
                         f"Stamina:\n\n"
                         
                         f"Gold:\n"
                         f"Carried items:\n"
                         f"Carry weight:\n"
                         , header=f"{target.get_display_name(capital=True)}")

        table.add_column(f"(Class)\n"
                         f"|w{target.db.level}|n\n"
                         f"|500{target.db.hp}/{target.get_max("hp")}|n\n"
                         f"|125{target.db.mana}/{target.get_max("mana")}|n\n"
                         f"|030{target.db.stamina}/{target.db.max_stam}|n\n\n"
                         
                         f"{appearance.gold}{target.db.gold}|n\n"
                         f"{target.carried_count()}/{target.db.max_carry_count}\n"
                         f"{target.encumbrance()}/{target.db.carry_weight}\n")

        table.add_column(f"Strength:\n"
                         f"Constitution:\n"
                         f"Dexterity:\n"
                         f"Perception:\n"
                         f"Intelligence:\n"
                         f"Wisdom:\n"
                         f"Spirit:\n\n")
        table.add_column(f"{appearance.highlight}{target.get_attr("str")}|n ({target.db.attribs["strength"]})\n"
                         f"{appearance.highlight}{target.get_attr("con")}|n ({target.db.attribs["constitution"]})\n"
                         f"{appearance.highlight}{target.get_attr("dex")}|n ({target.db.attribs["dexterity"]})\n"
                         f"{appearance.highlight}{target.get_attr("per")}|n ({target.db.attribs["perception"]})\n"
                         f"{appearance.highlight}{target.get_attr("int")}|n ({target.db.attribs["intelligence"]})\n"
                         f"{appearance.highlight}{target.get_attr("wis")}|n ({target.db.attribs["wisdom"]})\n"
                         f"{appearance.highlight}{target.get_attr("spi")}|n ({target.db.attribs["spirit"]})\n\n")

        table.add_column(f"Defense:\n"
                         f"Evasion:\n"
                         f"Resistance:\n\n"
                         
                         f"|wResists:|n\n"  
                         f"|=oBlunt: \n"
                         f"|=oSlashing: \n"
                         f"|=oPiercing: \n"
                         f"|=oFire: \n"
                         f"|=oCold: \n"
                         f"|=oShock: \n"
                         f"|=oPoison: \n")
        table.add_column(f"{display_resistances(target)}")

        self.caller.msg(table)


class StatsCmdSet(CmdSet):
    key = "PlayerCharacter"

    def at_cmdset_creation(self):
        super().at_cmdset_creation()
        self.add(CmdHP)
        self.add(CmdMana)
        self.add(CmdStamina)
        self.add(CmdStats)
