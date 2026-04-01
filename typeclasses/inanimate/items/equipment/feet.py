from typeclasses.inanimate.items.equipment.apparel import Footwear


class Footwraps(Footwear):
    def at_object_creation(self):
        super().at_object_creation()
        self.aliases.add("wraps")


class Boots(Footwear):
    def at_object_creation(self):
        super().at_object_creation()
        self.aliases.add("boots")


class Shoes(Footwear):
    def at_object_creation(self):
        super().at_object_creation()
        self.aliases.add("shoes")
