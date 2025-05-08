from typeclasses.inanimate.items.equipment.equipment import Equipment
from typeclasses.inanimate.items.usables import Usable


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
    pass


class Handaxe(OneHanded):
    pass


class Mace(OneHanded):
    pass


class Warhammer(TwoHanded):
    pass


class Greataxe(TwoHanded):
    pass


class Dagger(OneHanded):
    pass


class Quarterstaff(TwoHanded):
    pass


class Javelin(ThrownWeapon):
    pass


class Blowgun(RangedWeapon):
    pass


class Bow(RangedWeapon):
    pass


class Crossbow(RangedWeapon):
    pass


class Staff(MagicWeapon):
    pass


class Wand(MagicWeapon):
    pass
