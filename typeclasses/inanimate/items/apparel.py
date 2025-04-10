from typeclasses.inanimate.items.equipment import Equipment


class Apparel(Equipment):
    """
    Wearable, non-weapon equipment. May carry defense, evasion, resistance
    """

    def at_object_creation(self):
        """
        Called once, when this object is first created. This is the
        normal hook to overload for most object types.
        """
        super().at_object_creation()
        self.db.base_evasion = 0
        self.db.defense = 0
        self.db.resistance = 0

    def at_pre_drop(self, dropper, **kwargs):
        """
        Can't drop in combat.
        """
        if dropper.is_in_combat():
            dropper.msg("You can't doff armor in a fight!")
            return False
        return True

    def at_pre_give(self, giver, getter, **kwargs):
        """
        Can't give away in combat.
        """
        if giver.is_in_combat():
            giver.msg("You can't doff armor in a fight!")
            return False
        return True


class Shield(Apparel):
    """Secondary hand equipment for blocking damage."""

    def at_object_creation(self):
        super().at_object_creation()
        self.db.equipment_slot = "secondary"


class Headwear(Apparel):
    """Worn in the 'head' equipment slot."""

    def at_object_creation(self):
        super().at_object_creation()
        self.db.equipment_slot = "head"


class Neckwear(Apparel):
    """Worn in the 'neck' equipment slot."""

    def at_object_creation(self):
        super().at_object_creation()
        self.db.equipment_slot = "neck"


class Torsowear(Apparel):
    """Worn in the 'torso' equipment slot."""

    def at_object_creation(self):
        super().at_object_creation()
        self.db.equipment_slot = "torso"


class Bodywear(Apparel):
    """Worn in the 'about body' equipment slot."""

    def at_object_creation(self):
        super().at_object_creation()
        self.db.equipment_slot = "about body"


class Armwear(Apparel):
    """Worn in the 'arms' equipment slot."""

    def at_object_creation(self):
        super().at_object_creation()
        self.db.equipment_slot = "arms"


class Waistwear(Apparel):
    """Worn in the 'waist' equipment slot."""

    def at_object_creation(self):
        super().at_object_creation()
        self.db.equipment_slot = "waist"


class Legwear(Apparel):
    """Worn in the 'legs' equipment slot."""

    def at_object_creation(self):
        super().at_object_creation()
        self.db.equipment_slot = "legs"


class Footwear(Apparel):
    """Worn in the 'feet' equipment slot."""

    def at_object_creation(self):
        super().at_object_creation()
        self.db.equipment_slot = "feet"
