from server import appearance
from typeclasses.base.objects import Object
from typeclasses.scripts.item_scripts import TemporarilyHide


class Item(Object):

    def get_display_name(self, looker=None, **kwargs):
        return appearance.item + self.name + "|n"

    def get_display_desc(self, looker, **kwargs):
        return "This is an item."


class LightItem(Item):
    def get_display_desc(self, looker, **kwargs):
        return "An item that provides light."


class EndlessItem(Object):
    def at_pre_get(self, getter, **kwargs):
        new_obj = self.copy(new_key=self.key)
        new_obj.scripts.add(TemporarilyHide)
        return True


class EndlessLightItem(EndlessItem, LightItem):
    pass
