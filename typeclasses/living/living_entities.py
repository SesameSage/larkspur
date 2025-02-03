from evennia.objects.objects import DefaultCharacter

from typeclasses.base.objects import ObjectParent


class LivingEntity(ObjectParent, DefaultCharacter):
    """
    The Character just re-implements some of the Object's methods and hooks
    to represent a Character entity in-game.

    See mygame/typeclasses/objects.py for a list of
    properties and methods available on all Object child classes like this.

    """

    def announce_move_from(self, destination, msg=None, mapping=None, move_type="move", **kwargs):
        string = "{object} leaves {exit}."
        super().announce_move_from(destination=destination, mapping=mapping, move_type=move_type, msg=string, **kwargs)

    pass
