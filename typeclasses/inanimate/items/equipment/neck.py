from typeclasses.inanimate.items.equipment.apparel import Neckwear


class Necklace(Neckwear):
    def at_object_creation(self):
        super().at_object_creation()
        self.aliases.add("necklace")


class Choker(Neckwear):
    pass


class Coif(Neckwear):
    pass


class Talisman(Neckwear):
    pass
