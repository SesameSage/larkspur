from typeclasses.inanimate.items.item_types.equipment.apparel import Waistwear


class Belt(Waistwear):
    def at_object_creation(self):
        super().at_object_creation()
        self.aliases.add("belt")

class WaistPack(Waistwear):
    pass
