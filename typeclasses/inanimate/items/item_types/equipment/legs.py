from typeclasses.inanimate.items.item_types.equipment.apparel import Legwear


class Leggings(Legwear):
    def at_object_creation(self):
        super().at_object_creation()
        self.aliases.add("leggings")


class Greaves(Legwear):
    def at_object_creation(self):
        super().at_object_creation()
        self.aliases.add("greaves")
