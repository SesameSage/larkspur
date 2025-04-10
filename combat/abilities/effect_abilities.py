from combat.abilities.abilities import Ability
from combat.effects import SECS_PER_TURN, KnockedDown
from typeclasses.base.objects import Object
from typeclasses.living.living_entities import LivingEntity


class Sweep(Ability):
    """Attempts to knock an opponent down."""

    def at_object_creation(self):
        super().at_object_creation()
        self.db.targeted = True
        self.db.must_target_entity = True
        self.db.cost = ("stamina", 1)
        self.db.cooldown = 5 * SECS_PER_TURN

    def cast(self, caster: LivingEntity, target: Object = None):
        if not self.check(caster, target):
            return False
        if not super().cast(caster, target):
            return False
        weapon_weight = caster.get_weapon().db.weight if caster.get_weapon() else 0
        if target.get_attr("con") > caster.get_attr("str") + weapon_weight:
            caster.location.msg_contents(
                f"{target.get_display_name()} stands too strong for {caster.get_display_name()}'s"
                f" sweep of the legs!")
        elif target.get_attr("dex") > caster.get_attr("dex"):
            caster.location.msg_contents(
                f"{target.get_display_name()}'s quick footwork avoids {caster.get_display_name()}'s "
                f"sweep!")
        else:
            target.location.msg_contents(f"{caster.get_display_name()} sweeps at {target.get_display_name()}'s legs, "
                                         f"knocking them to the ground!")
            target.add_effect(KnockedDown)
        return True
