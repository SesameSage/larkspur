import evennia.prototypes.prototypes

from typeclasses.inanimate.items.items import Item


class Usable(Item):
    def at_object_creation(self):
        super().at_object_creation()
        self.db.use_effect = None


class Consumable(Usable):
    def at_object_creation(self):
        self.item_uses = 0
        self.item_func = None


class Potion(Consumable):
    pass
