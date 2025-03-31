from evennia import EvTable

from server import appearance
from typeclasses.inanimate.items.items import Item


class Usable(Item):
    def at_object_creation(self):
        super().at_object_creation()
        self.item_func = None

    def color(self):
        return appearance.usable

    def identify(self):
        table = EvTable()
        table.add_column(f"Weight: {self.db.weight}",
                         f"Average value: {self.db.avg_value}", header=self.get_display_name())
        item_func = self.db.item_func
        func_str = ""
        match item_func:
            case "add_effect":
                for effect in self.db.kwargs["effects"]:
                    func_str = func_str + "Add " + effect["effect_key"] + " "
            case "heal":
                func_str = "Heal"
            case "cure_condition":
                for effect in self.db.kwargs["effects_cured"]:
                    func_str = func_str + "Cure " + effect + " "

        table.add_column(f"Num. Uses: {self.db.item_uses}",
                         f"Function: {func_str}",
                         header=self.__class__.__name__)
        return table


class Consumable(Usable):
    def at_object_creation(self):
        super().at_object_creation()
        self.item_uses = 0


class Potion(Consumable):
    pass
