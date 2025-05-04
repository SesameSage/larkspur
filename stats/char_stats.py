from evennia.utils.evmenu import EvMenu

from server import appearance
from stats.stats_constants import XP_THRESHOLD_INCREASES, POINTS_GAINED_BY_LEVEL

ATTRIBUTES = {
    "strength": {
        "long_desc": "",
        "affects": "Affects: melee damage, carry weight, max stamina, and use of heavy equipment"
    },
    "constitution": {
        "long_desc": "",
        "affects": "Affects: physical defense, hitpoints, and stamina regeneration"
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
    },
    "wisdom": {
        "long_desc": "",
        "affects": "Affects: capability to use spells, magic resistance, mana regeneration, amount healed"
    },
    "spirit": {
        "long_desc": "",
        "affects": "Affects: spell power, maximum mana, hitpoint regeneration, and enchanting"
    }}


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


