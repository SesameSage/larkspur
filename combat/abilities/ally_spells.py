from combat.abilities.spells import Spell
from combat.effects import SECS_PER_TURN
from typeclasses.base.objects import Object
from typeclasses.living.living_entities import LivingEntity


class Revive(Spell):
    def at_object_creation(self):
        super().at_object_creation()
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


class Cleanse(Spell):
    def at_object_creation(self):
        super().at_object_creation()
        self.key = "Cleanse"
        self.db.desc = "Remove a temporary negative effect from an ally."
        self.db.targeted = True
        self.db.must_target_entity = True
        self.db.cost = ("mana", 12)
        self.db.cooldown = 5 * SECS_PER_TURN

    def func(self, caster: LivingEntity, target: Object = None):
        target.location.msg_contents(f"{caster.get_display_name(capital=True)} shines a cleansing light on "
                                     f"{target.get_display_name()}.")
        for script in target.scripts.all():
            if script.db.duration and not script.db.positive:
                script.add_seconds(amt=script.db.duration)
                script.check_duration()
                return True
        target.location.msg(f"Couldn't find a negative effect on {target.get_display_name()}!")
        return False
