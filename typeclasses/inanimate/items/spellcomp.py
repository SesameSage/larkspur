from typeclasses.inanimate.items.items import Item





class SpellComp(Item):
    def at_object_creation(self):
        super().at_object_creation()
        self.db.desc = "An ingredient used in spells and crafting."
        self.db.uses = {}

    def get_strength(self, use):
        return self.db.uses[use]
