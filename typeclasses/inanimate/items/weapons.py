from typeclasses.inanimate.items.items import Item


class Weapon(Item):

    def at_object_creation(self):
        self.db.damage_range = (15, 25)  # Minimum and maximum damage on hit
        self.db.accuracy_bonus = 0  # Bonus to attack rolls (or penalty if negative)
        self.db.weapon_type_name = (
            "weapon"  # Single word for weapon - I.E. "dagger", "staff", "scimitar"
        )

    def at_drop(self, dropper):
        """
        Stop being wielded if dropped.
        """
        if dropper.db.wielded_weapon == self:
            dropper.db.wielded_weapon = None
            dropper.location.msg_contents("%s stops wielding %s." % (dropper, self))

    def at_give(self, giver, getter):
        """
        Stop being wielded if given.
        """
        if giver.db.wielded_weapon == self:
            giver.db.wielded_weapon = None
            giver.location.msg_contents("%s stops wielding %s." % (giver, self))


class MeeleeWeapon(Weapon):
    pass


class Sword(MeeleeWeapon):
    pass


class GreatSword(MeeleeWeapon):
    pass


class Axe(MeeleeWeapon):
    pass


class Mace(MeeleeWeapon):
    pass


class WarHammer(MeeleeWeapon):
    pass


class Dagger(MeeleeWeapon):
    pass


class Quarterstaff(MeeleeWeapon):
    pass
