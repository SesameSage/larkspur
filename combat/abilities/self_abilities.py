from combat.abilities.abilities import Ability
from combat.effects import SECS_PER_TURN, DurationEffect, TimedStatMod
from typeclasses.base.objects import Object
from typeclasses.living.living_entities import LivingEntity


class EnergyTap(Ability):
    key = "Energy Tap"

    def at_object_creation(self):
        super().at_object_creation()
        self.db.desc = "Reinvigorate yourself with your opponents' stamina as you attack."
        self.db.targeted = False
        self.db.cost = ("mana", 12)
        self.db.cooldown = 8 * SECS_PER_TURN

    def func(self, caster: LivingEntity, target: Object = None):
        caster.location.msg_contents(f"{caster.get_display_name(capital=True)} adjusts their stance to redirect their "
                                     f"opponents' energy into their own attacks!")
        attributes = [("effect_key", "Siphon Stamina"), ("duration", 5 * SECS_PER_TURN), ("positive", True)]
        caster.add_effect(typeclass=DurationEffect, attributes=attributes)
        return True


class Expel(Ability):
    def at_object_creation(self):
        super().at_object_creation()
        self.db.desc = "Collect and expel the negative aura in your body to remove a temporary debuff."
        self.db.targeted = False
        self.db.cost = ("mana", 16)
        self.db.cooldown = 8 * SECS_PER_TURN

    def func(self, caster: LivingEntity, target: Object = None):
        caster.location.msg_contents(f"{caster.get_display_name(capital=True)} collects and expels negative aura.")
        for script in caster.scripts.all():
            if script.db.duration and not script.db.positive:
                script.add_seconds(amt=script.db.duration)
                script.check_duration()
                return True
        caster.location.msg(f"Couldn't find a negative effect on {target.get_display_name()}!")
        return False


class FocusMind(Ability):
    key = "Focus Mind"

    def at_object_creation(self):
        super().at_object_creation()
        self.db.desc = "Land your attacks more accurately with a calm and focused mind."
        self.db.targeted = False
        self.db.cost = ("stamina", 5)
        self.db.cooldown = 3 * SECS_PER_TURN

    def func(self, caster: LivingEntity, target: Object = None):
        caster.location.msg_contents(f"{caster.get_display_name(capital=True)} centers and focuses their mind.")
        attributes = [("effect_key", "+Accuracy"), ("amount", 20), ("duration", 3 * SECS_PER_TURN)]
        caster.add_effect(typeclass=TimedStatMod, attributes=attributes)
