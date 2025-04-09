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
