from typeclasses.scripts.scripts import Script
from typeclasses.inanimate.items.weapons import *


class CombatClass(Script):

    def at_script_creation(self):
        self.db.class_desc = ""
        self.db.equipment_types = []
        self.db.ability_tree = None


class Templar(CombatClass):
    def at_script_creation(self):
        super().at_script_creation()
        self.db.equipment_types = [Sword, GreatSword, HandAxe, Mace]


class Warden(CombatClass):
    def at_script_creation(self):
        super().at_script_creation()
        self.db.equipment_types = [Javelin, Crossbow]


class Gladiator(CombatClass):
    def at_script_creation(self):
        super().at_script_creation()
        self.db.equipment_types = [GreatSword, Greataxe, Warhammer]


class Monk(CombatClass):
    def at_script_creation(self):
        super().at_script_creation()
        self.db.equipment_types = [Dagger, Quarterstaff]


class Assassin(CombatClass):
    def at_script_creation(self):
        super().at_script_creation()
        self.db.equipment_types = [Sword, HandAxe, Dagger, Blowgun]


class Ranger(CombatClass):
    def at_script_creation(self):
        super().at_script_creation()
        self.db.equipment_types = [Blowgun, Bow, Crossbow]


class Druid(CombatClass):
    def at_script_creation(self):
        super().at_script_creation()
        self.db.equipment_types = [Quarterstaff, Blowgun]


class Cleric(CombatClass):
    def at_script_creation(self):
        super().at_script_creation()
        self.db.equipment_types = [Staff]


class Witch(CombatClass):
    def at_script_creation(self):
        super().at_script_creation()
        self.db.equipment_types = [Wand]


class Sorcerer(CombatClass):
    def at_script_creation(self):
        super().at_script_creation()
        self.db.equipment_types = [Staff, Wand]
