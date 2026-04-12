from typeclasses.inanimate.items.item_types.equipment.apparel import Bodywear


class Cape(Bodywear):
    def at_object_creation(self):
        super().at_object_creation()
        self.aliases.add("cape")


class Robe(Bodywear):
    def at_object_creation(self):
        super().at_object_creation()
        self.aliases.add("robe")


class Fur(Bodywear):
    pass


class Habit(Bodywear):
    pass


class Surcoat(Bodywear):
    pass


class Tabard(Bodywear):
    pass

