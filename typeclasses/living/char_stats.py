from evennia import Command, CmdSet
from evennia.utils.evmenu import EvMenu
from evennia.utils.evtable import EvTable

from combat.effects import DamageTypes
from server import appearance

ATTRIBUTES = {
    "strength": {
        "long_desc": "",
        "affects": "Affects: melee damage, carry weight, stamina, and use of heavy equipment"
    },
    "constitution": {
        "long_desc": "",
        "affects": "Affects: physical defense, hitpoints, and stamina"
    },
    "dexterity": {
        "long_desc": "",
        "affects": "Affects: evasion, maximum items carried, use of small and ranged weapons, and turn order"
    },
    "perception": {
        "long_desc": "",
        "affects": "Affects: attack accuracy and detection of sneaking enemies, traps, deception, hidden items, etc."
    },
    "intelligence": {
        "long_desc": "",
        "affects": "Affects: capability to use abilities, lockpicking, alchemy, trapmaking, deception, and deception "
                   "detection"
        # TODO: Attribute requirements for spells
    },
    "wisdom": {
        "long_desc": "",
        "affects": "Affects: capability to use spells, magic resistance, mana regeneration, amount healed"
    },
    "spirit": {
        "long_desc": "",
        "affects": "Affects: spell power, maximum mana, hitpoint regeneration, and enchanting"
    }}

XP_THRESHOLD_INCREASES = [
    (2, 100),
    (3, 150),
    (4, 225),
    (5, 350),
    (6, 500),
]
POINTS_GAINED_BY_LEVEL = {
    2: {"attribute": 1},
    3: {},
    4: {"attribute": 1},
    5: {},
    6: {"attribute": 1},
}


def xp_threshold(level: int):
    threshold = 0
    for i_level, increase in XP_THRESHOLD_INCREASES:
        if i_level > level:
            break
        threshold += increase
    return threshold


def xp_remaining(character, level: int):
    threshold = xp_threshold(level)
    last_threshold = xp_threshold(character.db.level)
    needed = threshold - last_threshold
    current_xp = character.db.xp
    toward_next_level = current_xp - last_threshold
    return needed - toward_next_level


def level_up(character):
    character.msg("You reflect on your experience and how your endeavors have honed your skills and traits.")
    character.db.level += 1
    new_level = character.db.level
    character.msg(f"{appearance.notify}You are now level {new_level}!")
    for attribute, amt in character.db.rpg_class.level_to_attributes[new_level]:
        character.db.attribs[attribute.lower()] += amt
        character.msg(f"{appearance.notify}Your {attribute} has increased by {amt}.")

    attr_points_gained = POINTS_GAINED_BY_LEVEL[new_level]["attribute"]
    if attr_points_gained:
        character.db.attr_points += attr_points_gained
        character.msg(f"{appearance.notify}You have {attr_points_gained} new attribute points!")

    spend_attribute_points(character)


def spend_attribute_points(character):
    menu_data = {"choose_attribute": choose_attribute, "end_node": end_node}
    EvMenu(caller=character, menudata=menu_data, startnode="choose_attribute", cmdset_mergetype='Union')


def choose_attribute(character):
    text = "Select which attribute to increase:"
    options = []
    for attribute in ATTRIBUTES:
        options.append({"key": (attribute.capitalize(), attribute[:3]),
                        "desc": f"({appearance.highlight}{character.db.attribs[attribute]}|n) "
                                f"|=m{ATTRIBUTES[attribute]["affects"]}\n",
                        "goto": (_increase_attribute, {"attribute": attribute})})
    options.append({"key": "Cancel",
                    "goto": "end_node"})
    options = tuple(options)
    return text, options


def _increase_attribute(character, **kwargs):
    attribute = kwargs.get("attribute")
    character.db.attribs[attribute] += 1
    character.msg(f"{appearance.notify}{attribute.capitalize()} increased to {character.db.attribs[attribute]}.")
    character.db.attr_points -= 1
    return "end_node"


def end_node(character, input, **kwargs):
    return


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
            stat_mapping = {target.get_defense: target.db.char_defense[None] if None in target.db.char_defense else 0,
                            target.get_evasion: target.db.char_evasion,
                            target.get_resistance: target.db.char_resistance[None] if None in target.db.char_resistance else 0}
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
                self.args, candidates=[content for content in self.caller.location.contents if content.attributes.has("hp")])
            if not target:
                self.caller.msg(f"Can't find '{self.args}' here")
                return
            if not target.attributes.has("hp"):
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


class CmdEffects(Command):
    key = "effects"
    aliases = "effect", "eff", "ef"
    help_category = "character"

    def func(self):
        if self.args:  # Target given
            target = self.caller.search(
                self.args, candidates=[content for content in self.caller.location.contents if content.db.hp])
            if not target:
                self.caller.msg(f"Can't find '{self.args}' here")
                return
            if not target.db.effects:
                self.caller.msg(f"{target.name.capitalize()} isn't affected by combat conditions!")
                return
        else:  # Show self effects
            target = self.caller

        table = EvTable("|wEffect", "|wAmount", "|wDuration")

        for effect in target.db.effects:
            name = effect
            effect = target.db.effects[effect]
            amount = effect["amount"] if "amount" in effect else "--"
            duration = effect["duration"] if "duration" in effect else "-"
            seconds_passed = effect["seconds passed"] if "seconds passed" in effect else "-"
            table.add_row(name, amount, f"{seconds_passed}/{duration}")

        self.caller.msg(table)


class CmdXP(Command):
    key = "xp"
    help_category = "character"

    def func(self):
        """
            show xp to next level

            Usage:
              xp

            Displays your total experience points gained, and your progress toward leveling up.
            """
        total = self.caller.db.xp
        next_level = self.caller.db.level + 1
        remaining = xp_remaining(self.caller, next_level)
        self.caller.msg(f"You have amassed {total} experience points.")
        self.caller.msg(f"You need {remaining} more XP to reach level {next_level}.")


class CmdLevelUp(Command):
    key = "level up"
    aliases = "level", "lev"
    help_category = "character"

    def func(self):
        """
            gain a level and increase stats

            Usage:
              level up

            When you have enough experience (XP) to increase your character's level, your character's stats will raise
            according to your character's class and your choices after performing this command.
            """
        caller = self.caller
        if caller.db.xp < xp_threshold(caller.db.level + 1):
            caller.msg("You do not have enough experience to level up!")
            return
        else:
            level_up(caller)


class StatsCmdSet(CmdSet):
    key = "PlayerCharacter"

    def at_cmdset_creation(self):
        super().at_cmdset_creation()
        self.add(CmdHP)
        self.add(CmdMana)
        self.add(CmdStamina)
        self.add(CmdStats)
        self.add(CmdEffects)
        self.add(CmdXP)
        self.add(CmdLevelUp)
