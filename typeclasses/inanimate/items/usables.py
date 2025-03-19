import evennia.prototypes.prototypes

from typeclasses.inanimate.items.items import Item


class Usable(Item):
    def at_object_creation(self):
        super().at_object_creation()
        self.item_func = None


class Consumable(Usable):
    def at_object_creation(self):
        super().at_object_creation()
        self.item_uses = 0


class Potion(Consumable):
    pass
