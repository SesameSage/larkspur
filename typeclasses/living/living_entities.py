from server import appearance
from typeclasses.base.objects import Object
from combat.combat_character import CombatEntity


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
        self.db.appear_string = f"A {self.get_display_name()} is here."

    def color(self):
        if self.db.hostile:
            return appearance.enemy
        else:
            return appearance.character

    def announce_move_from(self, destination, msg=None, mapping=None, move_type="move", **kwargs):
        # TODO: Make this work for non cardinal exits
        string = "{object}|=j leaves {exit}."
        super().announce_move_from(destination=destination, mapping=mapping, move_type=move_type, msg=string, **kwargs)


