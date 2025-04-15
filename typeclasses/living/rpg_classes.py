from typeclasses.inanimate.items.equipment.apparel import Shield
from typeclasses.inanimate.items.equipment.weapons import *
from typeclasses.scripts.scripts import Script


class CombatClass(Script):
    class_desc = ""
    equipment_types = []
    LEVEL_TO_ATTRIBUTES = {}
    ability_tree = None


class Templar(CombatClass):
    equipment_types = [Shield, Sword, GreatSword, HandAxe, Mace]
    LEVEL_TO_ATTRIBUTES = {1: [("Constitution", 1), ("Strength", 1)],
                           2: [("Wisdom", 1)],
                           3: [("Constitution", 1), ("Wisdom", 1)],
                           4: [("Strength", 1)],
                           5: [("Wisdom", 1), ("Constitution", 1)],
                           6: [("Wisdom", 1)]}


class Warden(CombatClass):
    equipment_types = [Shield, Javelin, Crossbow]
    LEVEL_TO_ATTRIBUTES = {1: [("Strength", 1), ("Dexterity", 1)],
                           2: [("Perception", 1), ("Strength", 1)],
                           3: [("Constitution", 1)],
                           4: [("Dexterity", 1), ("Strength", 1)],
                           5: [("Perception", 1)],
                           6: [("Strength", 1)]}


class Gladiator(CombatClass):
    equipment_types = [Shield, GreatSword, Greataxe, Warhammer]
    LEVEL_TO_ATTRIBUTES = {1: [("Strength", 1), ("Constitution", 1)],
                           2: [("Strength", 1)],
                           3: [("Constitution", 1)],
                           4: [("Spirit", 1), ("Strength", 1)],
                           5: [("Strength", 1), ("Constitution", 1)],
                           6: [("Wisdom", 1)]}


class Monk(CombatClass):
    equipment_types = [Dagger, Quarterstaff]
    LEVEL_TO_ATTRIBUTES = {1: [("Dexterity", 1), ("Wisdom", 1)],
                           2: [("Constitution", 1)],
                           3: [("Dexterity", 1)],
                           4: [("Wisdom", 1), ("Spirit", 1)],
                           5: [("Wisdom", 1)],
                           6: [("Dexterity", 1), ("Constitution", 1)]}


class Assassin(CombatClass):
    equipment_types = [Sword, HandAxe, Dagger, Blowgun]
    LEVEL_TO_ATTRIBUTES = {1: [("Dexterity", 1), ("Perception", 1)],
                           2: [("Intelligence", 1)],
                           3: [("Dexterity", 1), ("Perception", 1)],
                           4: [("Dexterity", 1), ("Intelligence", 1)],
                           5: [("Dexterity", 1)],
                           6: [("Intelligence", 1)]}


class Ranger(CombatClass):
    equipment_types = [Blowgun, Bow, Crossbow]
    LEVEL_TO_ATTRIBUTES = {1: [("Perception", 1), ("Dexterity", 1)],
                           2: [("Dexterity", 1), ("Intelligence", 1)],
                           3: [("Perception", 1)],
                           4: [("Dexterity", 1), ("Intelligence", 1)],
                           5: [("Perception", 1)],
                           6: [("Perception", 1)]}


class Druid(CombatClass):
    class_desc = "Druids shapeshift into other natural forms to see the unseen, reach the unreachable, take"
    " advantage of the natural environment, and choose on-the-spot from a versatile array of combat strategies."
    " \n\nThe most important recommended attributes for a druid are wisdom, intelligence, and spirit."
    equipment_types = [Quarterstaff, Blowgun]
    LEVEL_TO_ATTRIBUTES = {1: [("Wisdom", 1), ("Spirit", 1)],
                           2: [("Intelligence", 1)],
                           3: [("Spirit", 1)],
                           4: [("Wisdom", 1), ("Intelligence", 1)],
                           5: [("Wisdom", 1)],
                           6: [("Wisdom", 1), ("Intelligence", 1)]}


class Cleric(CombatClass):
    equipment_types = [Staff]
    LEVEL_TO_ATTRIBUTES = {1: [("Spirit", 1), ("Wisdom", 1)],
                           2: [("Spirit", 1)],
                           3: [("Wisdom", 1), ("Constitution", 1)],
                           4: [("Spirit", 1)],
                           5: [("Spirit", 1), ("Constitution", 1)],
                           6: [("Wisdom", 1)]}


class Witch(CombatClass):
    equipment_types = [Wand, Dagger]
    LEVEL_TO_ATTRIBUTES = {1: [("Wisdom", 1), ("Spirit", 1)],
                           2: [("Perception", 1)],
                           3: [("Wisdom", 1)],
                           4: [("Spirit", 1), ("Perception", 1)],
                           5: [("Wisdom", 1), ("Spirit", 1)],
                           6: [("Perception", 1)]}


class Sorcerer(CombatClass):
    equipment_types = [Staff, Wand]
    LEVEL_TO_ATTRIBUTES = {1: [("Spirit", 1), ("Wisdom", 1)],
                           2: [("Spirit", 1), ("Wisdom", 1)],
                           3: [("Spirit", 1)],
                           4: [("Spirit", 1), ("Wisdom", 1)],
                           5: [("Spirit", 1)],
                           6: [("Intelligence", 1)]}


def get_attributes(rpg_class, level: int):
    attributes = {"strength": 1, "constitution": 1, "dexterity": 1, "perception": 1,
                  "intelligence": 1, "wisdom": 1, "spirit": 1}
    for i_level in rpg_class.LEVEL_TO_ATTRIBUTES:
        if i_level > level:
            break
        else:
            for attr_to_add, amt in rpg_class.LEVEL_TO_ATTRIBUTES[i_level]:
                attributes[attr_to_add.lower()] += amt
    return attributes
