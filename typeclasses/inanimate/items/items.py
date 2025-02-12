from server import appearance
from typeclasses.base.objects import Object
from typeclasses.scripts.item_scripts import TemporarilyHide


class Item(Object):

    def at_object_creation(self):
        self.db.desc = "This is an item."

    def get_display_name(self, looker=None, **kwargs):
        return appearance.item + self.name + "|n"


class LightItem(Item):
    def at_object_creation(self):
        self.db.desc = "An item that provides light."


class EndlessItem(Object):
    def at_pre_get(self, getter, **kwargs):
        new_obj = self.copy(new_key=self.key)
        new_obj.scripts.add(TemporarilyHide)
        return True


class EndlessLightItem(EndlessItem, LightItem):
    pass
