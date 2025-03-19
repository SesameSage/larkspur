from server import appearance
from typeclasses.base.objects import Object


class Item(Object):

    def at_object_creation(self):
        super().at_object_creation()
        self.db.desc = "This is an item."
        self.db.weight = 0.0
        self.db.avg_value = 0.0

    def get_display_name(self, looker=None, capital=False, **kwargs):
        name = self.name
        if capital:
            name = name.capitalize()
        return appearance.item + name + "|n"


class LightItem(Item):
    def at_object_creation(self):
        super().at_object_creation()
        self.db.desc = "An item that provides light."
