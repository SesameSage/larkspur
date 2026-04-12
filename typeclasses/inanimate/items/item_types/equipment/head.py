from typeclasses.inanimate.items.item_types.equipment.apparel import Headwear

class Helmet(Headwear):
    def at_object_creation(self):
        super().at_object_creation()
        self.aliases.add("helmet")


class Hood(Headwear):
    def at_object_creation(self):
        super().at_object_creation()
        self.aliases.add("hood")


class Circlet(Headwear):
    def at_object_creation(self):
        super().at_object_creation()
        self.aliases.add("circlet")
