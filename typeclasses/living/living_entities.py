from server import appearance
from turnbattle.tb_custom import TurnBattleCharacter
from typeclasses.base.objects import ObjectParent


class LivingEntity(ObjectParent, TurnBattleCharacter):
    """
    The Character just re-implements some of the Object's methods and hooks
    to represent a Character entity in-game.

    See mygame/typeclasses/objects.py for a list of
    properties and methods available on all Object child classes like this.

    """

    def at_object_creation(self):
        super().at_object_creation()
        self.db.attribs = {"Strength": 0, "Dexterity": 0}
        self.db.hostile = False

    def announce_move_from(self, destination, msg=None, mapping=None, move_type="move", **kwargs):
        string = "{object}|=j leaves {exit}."
        super().announce_move_from(destination=destination, mapping=mapping, move_type=move_type, msg=string, **kwargs)

    pass


class Enemy(LivingEntity):
    def at_object_creation(self):
        super().at_object_creation()
        self.db.hostile = True

    def get_display_name(self, looker=None, **kwargs):
        return appearance.enemy + super().get_display_name(looker=looker) + "|n"


class Cultist(Enemy):
    pass
