from typeclasses.inanimate.items.item_types.equipment.equipment import Equipment
from typeclasses.inanimate.items.item_types.usables import Usable


class Weapon(Equipment):

    def at_object_creation(self):
        super().at_object_creation()
        self.db.damage_ranges = {}  # Minimum and maximum damage on hit
        self.db.accuracy_buff = 0  # Bonus to attack rolls (or penalty if negative)
        self.db.equipment_slot = "primary"
        # TODO: Secondary holding slot


class MeleeWeapon(Weapon):
    def at_object_creation(self):
        super().at_object_creation()
        self.db.range = 1


class OneHanded(MeleeWeapon):
    pass


class TwoHanded(MeleeWeapon):
    pass


class RangedWeapon(Weapon):
    pass


class ThrownWeapon(Usable):
    pass


class MagicWeapon(Weapon):
    pass


class Sword(OneHanded):
    pass


class Greatsword(TwoHanded):
    def at_object_creation(self):
        super().at_object_creation()
        self.aliases.add("sword")


class Handaxe(OneHanded):
    def at_object_creation(self):
        super().at_object_creation()
        self.aliases.add("axe")


class Mace(OneHanded):
    pass


class Warhammer(TwoHanded):
    def at_object_creation(self):
        super().at_object_creation()
        self.aliases.add("hammer")


class Greataxe(TwoHanded):
    def at_object_creation(self):
        super().at_object_creation()
        self.aliases.add("axe")


class Dagger(OneHanded):
    pass


class Quarterstaff(TwoHanded):
    def at_object_creation(self):
        super().at_object_creation()
        self.aliases.add("staff")


class Javelin(ThrownWeapon):
    pass


class Blowgun(RangedWeapon):
    pass


class Bow(RangedWeapon):
    class MeleeWeapon(Weapon):
        def at_object_creation(self):
            super().at_object_creation()
            self.db.range = 10


class Crossbow(RangedWeapon):
    pass


class Staff(MagicWeapon):
    pass


class Wand(MagicWeapon):
    pass
