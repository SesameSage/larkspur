from decimal import Decimal as Dec

from evennia.utils.evtable import EvTable

from server import appearance
from typeclasses.base.objects import Object
from combat.combat_character import CombatEntity
from typeclasses.inanimate.items.items import Item

BASE_CARRY_WEIGHT = Dec(30)
STR_TO_CARRY_WEIGHT = {
    1: Dec(0),
    2: Dec(5),
    3: Dec(10),
    4: Dec(20),
    5: Dec(35),
    6: Dec(55),
    7: Dec(80),
}
BASE_CARRY_COUNT = 10
DEX_TO_CARRY_COUNT = {
    1: 0,
    2: 2,
    3: 3,
    4: 5,
    5: 7,
    6: 10,
}


class LivingEntity(Object, CombatEntity):
    """
    Somthing that can move around and be killed.
    """

    def at_object_creation(self):
        super().at_object_creation()
        self.db.gold = 0
        self.appearance_template = """
{header}
|c{name}{extra_name_info}|n
{desc}
{things}
{footer}
    """
        self.db.appear_string = f"{self.get_display_name(article=True).capitalize()} is here."

        self.db.carry_weight = BASE_CARRY_WEIGHT
        self.db.max_carry_count = BASE_CARRY_COUNT

    def color(self):
        if self.db.hostile:
            return appearance.enemy
        else:
            return appearance.character

    def carried_count(self):
        carried_count = 0
        for item in self.contents:
            if isinstance(item, Item):
                carried_count += 1
        return carried_count

    def encumbrance(self):
        encumbrance = Dec(0)
        for item in self.contents:
            if isinstance(item, Item):
                if item.contents:
                    for content in item.contents:
                        encumbrance += content.db.weight
                encumbrance += item.db.weight

        return encumbrance

    def table_carry_limits(self):
        table = EvTable(border=None)
        table.add_row(self.caller.carried_count(), "/", self.caller.db.max_carry_count, "items")
        table.add_row(format(self.caller.encumbrance(), ".2g"), "/", self.caller.db.carry_weight, "weight")
        return table

    def announce_move_from(self, destination, msg=None, mapping=None, move_type="move", **kwargs):
        # TODO: Make this work for non cardinal exits
        string = "{object}|=j leaves {exit}."
        super().announce_move_from(destination=destination, mapping=mapping, move_type=move_type, msg=string, **kwargs)
