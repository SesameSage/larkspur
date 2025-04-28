from combat.abilities.effect_abilities import Sweep, NeutralizingHum
from typeclasses.inanimate.items.equipment.apparel import Shield
from typeclasses.inanimate.items.equipment.weapons import *
from typeclasses.scripts.scripts import Script


class CombatClass(Script):
    class_desc = ""
    equipment_types = []
    level_to_attributes = {}
    ability_tree = None


class Templar(CombatClass):
    equipment_types = [Shield, Sword, GreatSword, HandAxe, Mace]
    level_to_attributes = {1: [("Constitution", 1), ("Strength", 1)],
                           2: [("Wisdom", 1)],
                           3: [("Constitution", 1), ("Wisdom", 1)],
                           4: [("Strength", 1)],
                           5: [("Wisdom", 1), ("Constitution", 1)],
                           6: [("Wisdom", 1)]}


class Warden(CombatClass):
    equipment_types = [Shield, Javelin, Crossbow]
    level_to_attributes = {1: [("Strength", 1), ("Dexterity", 1)],
                           2: [("Perception", 1), ("Strength", 1)],
                           3: [("Constitution", 1)],
                           4: [("Dexterity", 1), ("Strength", 1)],
                           5: [("Perception", 1)],
                           6: [("Strength", 1)]}


class Gladiator(CombatClass):
    equipment_types = [Shield, GreatSword, Greataxe, Warhammer]
    level_to_attributes = {1: [("Strength", 1), ("Constitution", 1)],
                           2: [("Strength", 1)],
                           3: [("Constitution", 1)],
                           4: [("Spirit", 1), ("Strength", 1)],
                           5: [("Strength", 1), ("Constitution", 1)],
                           6: [("Wisdom", 1)]}


class Assassin(CombatClass):
    equipment_types = [Sword, HandAxe, Dagger, Blowgun]
    level_to_attributes = {1: [("Dexterity", 1), ("Perception", 1)],
                           2: [("Intelligence", 1)],
                           3: [("Dexterity", 1), ("Perception", 1)],
                           4: [("Dexterity", 1), ("Intelligence", 1)],
                           5: [("Dexterity", 1)],
                           6: [("Intelligence", 1)]}


class Ranger(CombatClass):
    equipment_types = [Blowgun, Bow, Crossbow]
    level_to_attributes = {1: [("Perception", 1), ("Dexterity", 1)],
                           2: [("Dexterity", 1), ("Intelligence", 1)],
                           3: [("Perception", 1)],
                           4: [("Dexterity", 1), ("Intelligence", 1)],
                           5: [("Perception", 1)],
                           6: [("Perception", 1)]}


class Monk(CombatClass):
    equipment_types = [Dagger, Quarterstaff]
    level_to_attributes = {1: [("Dexterity", 1), ("Wisdom", 1)],
                           2: [("Constitution", 1)],
                           3: [("Dexterity", 1)],
                           4: [("Wisdom", 1), ("Spirit", 1)],
                           5: [("Wisdom", 1)],
                           6: [("Dexterity", 1), ("Constitution", 1)]}
    ability_tree = {1: (Sweep, NeutralizingHum)}


class Sorcerer(CombatClass):
    equipment_types = [Staff, Wand]
    level_to_attributes = {1: [("Spirit", 1), ("Wisdom", 1)],
                           2: [("Spirit", 1), ("Wisdom", 1)],
                           3: [("Spirit", 1)],
                           4: [("Spirit", 1), ("Wisdom", 1)],
                           5: [("Spirit", 1)],
                           6: [("Intelligence", 1)]}


class Cleric(CombatClass):
    equipment_types = [Staff]
    level_to_attributes = {1: [("Spirit", 1), ("Wisdom", 1)],
                           2: [("Spirit", 1)],
                           3: [("Wisdom", 1), ("Constitution", 1)],
                           4: [("Spirit", 1)],
                           5: [("Spirit", 1), ("Constitution", 1)],
                           6: [("Wisdom", 1)]}


class Druid(CombatClass):
    class_desc = "Druids shapeshift into other natural forms to see the unseen, reach the unreachable, take"
    " advantage of the natural environment, and choose on-the-spot from a versatile array of combat strategies."
    " \n\nThe most important recommended attributes for a druid are wisdom, intelligence, and spirit."
    equipment_types = [Quarterstaff, Blowgun]
    level_to_attributes = {1: [("Wisdom", 1), ("Spirit", 1)],
                           2: [("Intelligence", 1)],
                           3: [("Spirit", 1)],
                           4: [("Wisdom", 1), ("Intelligence", 1)],
                           5: [("Wisdom", 1)],
                           6: [("Wisdom", 1), ("Intelligence", 1)]}


class Witch(CombatClass):
    equipment_types = [Wand, Dagger]
    level_to_attributes = {1: [("Wisdom", 1), ("Spirit", 1)],
                           2: [("Perception", 1)],
                           3: [("Wisdom", 1)],
                           4: [("Spirit", 1), ("Perception", 1)],
                           5: [("Wisdom", 1), ("Spirit", 1)],
                           6: [("Perception", 1)]}


RPG_CLASSES = [Templar, Warden, Gladiator, Assassin, Ranger, Monk, Sorcerer, Cleric, Druid, Witch]


def get_attributes(rpg_class, level: int):
    attributes = {"strength": 1, "constitution": 1, "dexterity": 1, "perception": 1,
                  "intelligence": 1, "wisdom": 1, "spirit": 1}
    for i_level in rpg_class.level_to_attributes:
        if i_level > level:
            break
        else:
            for attr_to_add, amt in rpg_class.level_to_attributes[i_level]:
                attributes[attr_to_add.lower()] += amt
    return attributes
