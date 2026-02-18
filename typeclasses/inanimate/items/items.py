from decimal import Decimal as Dec

from evennia import EvTable

from server import appearance
from typeclasses.base.objects import Object


class Item(Object):

    def at_object_creation(self):
        super().at_object_creation()
        self.db.desc = "This is an item."
        self.db.weight = Dec(0)
        self.db.avg_value = 0.0
        self.db.range = 0

        self.db.quest_hooks = {"at_get": {}, "at_give": {}}

    def color(self):
        return appearance.item

    def identify(self):
        """Return a table containing details on the item such as its stats and effects."""
        table = EvTable(self.get_display_name(), (self.color() + self.__class__.__name__), pretty_corners=True)
        table.add_row(f"Weight: {self.db.weight}")
        table.add_row(f"Average value: {appearance.gold}{self.db.avg_value}|n")
        return table

    def at_get(self, getter, **kwargs):
        super().at_get(getter, **kwargs)
        hooks = self.db.quest_hooks["at_get"]
        for qid in hooks:
            for stage in hooks[qid]:
                hook_data = hooks[qid][stage]
                if getter.attributes.has("quest_stages") and getter.quests.at_stage(qid, stage):
                    getter.msg(hook_data["msg"])
                    getter.quests.advance_quest(hook_data["next_stage"])

    def at_give(self, giver, getter, **kwargs):
        super().at_give(giver, getter, **kwargs)
        hooks = self.db.quest_hooks["at_give"]
        for qid in hooks:
            for stage in hooks[qid]:
                hook_data = hooks[qid][stage]
                if getter.attributes.has("quest_stages") and getter.quests.at_stage(qid, stage):
                    getter.msg(hook_data["msg"])
                    getter.quests.advance_quest(hook_data["next_stage"])


class LightItem(Item):
    """An item that provides light."""

    def at_object_creation(self):
        super().at_object_creation()
        self.db.desc = "An item that provides light."
