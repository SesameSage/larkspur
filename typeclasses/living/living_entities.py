from server import appearance
from typeclasses.base.objects import Object
from typeclasses.living.combat_character import TurnBattleEntity


class LivingEntity(Object, TurnBattleEntity):
    """
    The Character just re-implements some of the Object's methods and hooks
    to represent a Character entity in-game.

    See mygame/typeclasses/objects.py for a list of
    properties and methods available on all Object child classes like this.

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
        self.db.appear_string = f"A {self.name} is here."

    def announce_move_from(self, destination, msg=None, mapping=None, move_type="move", **kwargs):
        string = "{object}|=j leaves {exit}."
        super().announce_move_from(destination=destination, mapping=mapping, move_type=move_type, msg=string, **kwargs)


class Enemy(LivingEntity):
    def at_object_creation(self):
        super().at_object_creation()
        self.db.hostile = True
        # TODO: Hostility to specific characters

    def color(self):
        return appearance.enemy


