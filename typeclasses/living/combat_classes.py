from typeclasses.scripts.scripts import Script


class CombatClass(Script):

    def at_script_creation(self):
        self.db.class_desc = ""
        self.db.weapon_types = []
        self.db.ability_tree = None


class Templar(CombatClass):
    pass


class Warden(CombatClass):
    pass


# Beserker?

class Monk(CombatClass):
    pass


class Assassin(CombatClass):
    pass


class Ranger(CombatClass):
    pass


class Druid(CombatClass):
    pass


class Cleric(CombatClass):
    pass


class Witch(CombatClass):
    pass


class Sorcerer(CombatClass):
    pass
