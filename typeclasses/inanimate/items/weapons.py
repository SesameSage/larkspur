from typeclasses.inanimate.items.items import Item


class Weapon(Item):

    def at_object_creation(self):
        pass

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
