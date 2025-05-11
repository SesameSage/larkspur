from evennia.utils.create import create_object

from server import appearance
from typeclasses.inanimate.items.containers import Container
from typeclasses.inanimate.gold import generate_gold_object
from typeclasses.scripts.item_scripts import TemporarilyHide


def make_corpse(entity):
    if not entity.db.dies:
        entity.location.msg(appearance.warning + "Can't make a corpse of an entity that knocks out instead of dying!")
        return

    key = f"the corpse of {entity.get_display_name(article=True)}"

    contents = [item for item in entity.contents if item.attributes.has("weight")]
    if entity.db.gold:
        contents.append(generate_gold_object(entity.db.gold))

    corpse = create_object(typeclass=Corpse, key=key, location=entity.location)

    for item in contents:
        item.move_to(corpse, quiet=True)


def set_to_respawn(entity):
    if not entity.db.dies:
        entity.location.msg(appearance.warning + "Tried to set an entity that knocks out to die and respawn!")
        return
    if entity.db.hp > 0:
        entity.location.msg(appearance.warning + "Tried to hide and set for respawn an entity with HP over 0!")
        return

    entity.move_to(entity.home)
    entity.scripts.add(TemporarilyHide())
    # Spawn new loot from table


class Corpse(Container):

    def at_object_creation(self):
        self.db.plural_name = True
        self.db.capacity = 20
        self.locks.add("get_from:all()")
