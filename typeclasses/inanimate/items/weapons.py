from typeclasses.inanimate.items.equipment import Equipment


class Weapon(Equipment):

    def at_object_creation(self):
        super().at_object_creation()
        self.db.weapon_type = None
        self.db.damage_ranges = {}  # Minimum and maximum damage on hit
        self.db.accuracy_bonus = 0  # Bonus to attack rolls (or penalty if negative)
        self.db.equipment_slot = "primary"

    def at_drop(self, dropper, **kwargs):
        """
        Stop being wielded if dropped.
        """
        if dropper.db.wielded_weapon == self:
            dropper.db.wielded_weapon = None
            dropper.location.msg_contents("%s stops wielding %s." % (dropper, self))

    def at_give(self, giver, getter, **kwargs):
        """
        Stop being wielded if given.
        """
        if giver.db.wielded_weapon == self:
            giver.db.wielded_weapon = None
            giver.location.msg_contents("%s stops wielding %s." % (giver, self))


class MeleeWeapon(Weapon):
    pass


class OneHanded(MeleeWeapon):
    pass


class TwoHanded(MeleeWeapon):
    pass


class RangedWeapon(Weapon):
    pass


class MagicWeapon(Weapon):
    pass


class Sword(OneHanded):
    pass


class GreatSword(TwoHanded):
    pass


class HandAxe(OneHanded):
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


class Javelin(RangedWeapon):
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
