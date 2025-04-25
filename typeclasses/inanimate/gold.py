from evennia.utils.create import create_object

from server import appearance
from typeclasses.inanimate.items.items import Item


def generate_gold_object(amount: int):
    return create_object(typeclass=Gold, key=f"{amount} gold", attributes=[("amount", amount), ("plural_name", True)])


class Gold(Item):
    def at_object_creation(self):
        self.db.amount = 1

    def color(self):
        return appearance.gold

    def at_get(self, getter, **kwargs):
        getter.db.gold += self.db.amount
        self.delete()
