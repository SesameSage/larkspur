from typeclasses.inanimate.items.equipment import Equipment


class Apparel(Equipment):
    """
    A set of armor which can be worn with the 'don' command.
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
        if dropper.rules.is_in_combat(dropper):
            dropper.msg("You can't doff armor in a fight!")
            return False
        return True

    def at_drop(self, dropper, **kwargs):
        """
        Stop being wielded if dropped.
        """
        if self.db.equipped:
            self.unequip(dropper)
        if dropper.db.equipment[self.db.equipment_slot] == self:
            dropper.db.equipmnt[self.db.equipment_slot] = None
            dropper.location.msg_contents("%s unequips %s." % (dropper, self))

    def at_pre_give(self, giver, getter, **kwargs):
        """
        Can't give away in combat.
        """
        if self.rules.is_in_combat(giver):
            giver.msg("You can't doff armor in a fight!")
            return False
        return True

    def at_give(self, giver, getter, **kwargs):
        """
        Stop being worn if given.
        """
        if giver.db.worn_armor == self:
            giver.db.worn_armor = None
            giver.location.msg_contents("%s removes %s." % (giver, self))
