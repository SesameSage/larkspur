from combat.abilities.abilities import Ability
from combat.effects import SECS_PER_TURN, KnockedDown
from typeclasses.base.objects import Object
from typeclasses.living.living_entities import LivingEntity


class Sweep(Ability):
    """Attempts to knock an opponent down."""

    def at_object_creation(self):
        super().at_object_creation()
        self.key = "Sweep"
        self.db.targeted = True
        self.db.must_target_entity = True
        self.db.cost = ("stamina", 1)
        self.db.cooldown = 5 * SECS_PER_TURN

    def func(self, caster: LivingEntity, target: Object = None):
        weapon_weight = caster.get_weapon().db.weight if not isinstance(caster.get_weapon(), str) else 0
        if target.get_attr("con") > caster.get_attr("str") + weapon_weight:
            caster.location.msg_contents(
                f"{target.get_display_name(capital=True)} stands too strong for {caster.get_display_name(article=True)}'s"
                f" sweep of the legs!")
        elif target.get_attr("dex") > caster.get_attr("dex"):
            caster.location.msg_contents(
                f"{target.get_display_name(capital=True)}'s quick footwork avoids {caster.get_display_name(article=True)}'s "
                f"sweep!")
        else:
            target.location.msg_contents(f"{caster.get_display_name()} sweeps at {target.get_display_name()}'s legs, "
                                         f"knocking them to the ground!")
            target.add_effect(KnockedDown)
        return True


class NeutralizingHum(Ability):
    key = "Neutralizing Hum"

    def at_object_creation(self):
        super().at_object_creation()
        self.db.targeted = False
        self.db.cost = ("mana", 10)
        self.db.cooldown = 10 * SECS_PER_TURN

    def func(self, caster: LivingEntity, target: Object = None):
        caster.location.msg_contents(
            f"{caster.get_display_name(capital=True)} emits a low, guttural throat-singing tone.")

        for entity in caster.location.contents:
            if entity.attributes.has("hostile") and entity.db.hostile != caster.db.hostile:
                if entity.get_resistance(None) < 20:
                    entity.db.mana -= 25
                    if entity.db.mana < 0:
                        entity.db.mana = 0
                    entity.location.msg_contents(f"{entity.get_display_name(capital=True)}'s mana has been drained!")
                else:
                    entity.location.msg_contents(
                        f"{entity.get_display_name(capital=True)} resists {self.get_display_name()}!")

        return True
