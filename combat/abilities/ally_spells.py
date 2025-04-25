from combat.abilities.spells import Spell
from combat.effects import SECS_PER_TURN
from typeclasses.base.objects import Object
from typeclasses.living.living_entities import LivingEntity


class Revive(Spell):
    def at_object_creation(self):
        super().at_object_creation()
        self.key = "Revive"
        self.db.desc = "Bring back an ally who has been knocked out."
        self.db.targeted = True
        self.db.must_target_entity = True
        self.db.cost = ("mana", 12)
        self.db.cooldown = 10 * SECS_PER_TURN

    def check(self, caster, target):
        if not super().check(caster, target):
            return False

        if target.db.hp > 0:
            caster.msg(target.name + " isn't knocked out!")
            return False

        return True

    def func(self, caster: LivingEntity, target: Object = None):
        target.db.hp = 50
        target.location.msg_contents(target.get_display_name() + " has been revived!")
