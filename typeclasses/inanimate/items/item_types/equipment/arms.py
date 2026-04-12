from typeclasses.inanimate.items.item_types.equipment.apparel import Armwear


class Bracers(Armwear):
    def at_object_creation(self):
        super().at_object_creation()
        self.aliases.add("bracers")


class Gauntlets(Armwear):
    def at_object_creation(self):
        super().at_object_creation()
        self.aliases.add("gauntlets")

