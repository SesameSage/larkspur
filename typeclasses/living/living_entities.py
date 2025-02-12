from server import appearance
from turnbattle.combat_character import TurnBattleCharacter
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
        self.db.equipment = {
            "primary": None,
            "secondary": None,
            "head": None,
            "neck": None,
            "torso": None,
            "about body": None,
            "arms": None,
            # TODO: Rings
            "waist": None,
            "legs": None,
            "feet": None
        }

    def announce_move_from(self, destination, msg=None, mapping=None, move_type="move", **kwargs):
        string = "{object}|=j leaves {exit}."
        super().announce_move_from(destination=destination, mapping=mapping, move_type=move_type, msg=string, **kwargs)

    def show_equipment(self, looker=None):
        if not looker:
            looker = self
        msg = ""
        for slot in self.db.equipment:
            if self.db.equipment[slot]:
                equipment = self.db.equipment[slot].get_display_name()
            else:
                equipment = "|=j---|n"
            msg += f"{slot}: {equipment}\n"
        return msg


class Enemy(LivingEntity):
    def at_object_creation(self):
        super().at_object_creation()
        self.db.hostile = True

    def get_display_name(self, looker=None, **kwargs):
        return appearance.enemy + super().get_display_name(looker=looker) + "|n"


class Cultist(Enemy):
    pass
