from server import appearance
from typeclasses.base.objects import Object


# TODO: Command identify
class Item(Object):

    def at_object_creation(self):
        super().at_object_creation()
        self.db.desc = "This is an item."
        self.db.weight = 0.0
        self.db.avg_value = 0.0

    def get_display_name(self, looker=None, **kwargs):
        return appearance.item + self.name + "|n"


class LightItem(Item):
    def at_object_creation(self):
        super().at_object_creation()
        self.db.desc = "An item that provides light."
