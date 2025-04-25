from evennia.utils.create import create_object

from combat.combat_character import CombatEntity
from typeclasses.inanimate.items.containers import Container
from typeclasses.inanimate.gold import generate_gold_object


def make_corpse(entity: CombatEntity):
    key = f"the corpse of {entity.get_display_name(article=True)}"
    contents = [item for item in entity.contents if item.attributes.has("weight")]
    if entity.db.gold:
        contents.append(generate_gold_object(entity.db.gold))
    corpse = create_object(typeclass=Corpse, key=key, location=entity.location)
    for item in contents:
        item.move_to(corpse, quiet=True)


class Corpse(Container):
    def at_object_creation(self):
        self.db.plural_name = True
