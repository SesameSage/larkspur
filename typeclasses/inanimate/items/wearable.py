from evennia.contrib.game_systems.clothing import ContribClothing


class Wearable(ContribClothing):
    pass


class Equipment(Wearable):
    """
    A set of armor which can be worn with the 'don' command.
    """

    def at_object_creation(self):
        """
        Called once, when this object is first created. This is the
        normal hook to overload for most object types.
        """
        self.db.damage_reduction = 4  # Amount of incoming damage reduced by armor
        self.db.defense_modifier = (
            -4
        )  # Amount to modify defense value (pos = harder to hit, neg = easier)

    def at_pre_drop(self, dropper):
        """
        Can't drop in combat.
        """
        if self.rules.is_in_combat(dropper):
            dropper.msg("You can't doff armor in a fight!")
            return False
        return True

    def at_drop(self, dropper):
        """
        Stop being wielded if dropped.
        """
        if dropper.db.worn_armor == self:
            dropper.db.worn_armor = None
            dropper.location.msg_contents("%s removes %s." % (dropper, self))

    def at_pre_give(self, giver, getter):
        """
        Can't give away in combat.
        """
        if self.rules.is_in_combat(giver):
            giver.msg("You can't doff armor in a fight!")
            return False
        return True

    def at_give(self, giver, getter):
        """
        Stop being wielded if given.
        """
        if giver.db.worn_armor == self:
            giver.db.worn_armor = None
            giver.location.msg_contents("%s removes %s." % (giver, self))
