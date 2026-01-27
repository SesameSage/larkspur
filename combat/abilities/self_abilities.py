"""Abilities used on oneself."""

from combat.abilities.abilities import Ability
from combat.effects import DurationEffect, TimedStatMod, DamageTypes
from combat.combat_constants import SECS_PER_TURN
from typeclasses.base.objects import Object
from typeclasses.living.living_entities import LivingEntity


class EnergyTap(Ability):
    key = "Energy Tap"
    desc = "Reinvigorate yourself with your opponents' stamina as you attack."

    def at_object_creation(self):
        super().at_object_creation()
        self.db.targeted = False
        self.db.offensive = False
        self.db.range = 0

        self.db.requires = [("wisdom", 2)]
        self.db.ap_cost = 1
        self.db.cost = [("mana", 12)]
        self.db.cooldown = 8 * SECS_PER_TURN

    def func(self, caster: LivingEntity, target: Object = None):
        caster.location.msg_contents(f"{caster.get_display_name(capital=True)} adjusts their stance to redirect their "
                                     f"opponents' energy into their own attacks!")
        attributes = [("effect_key", "Siphon Stamina"), ("duration", 5 * SECS_PER_TURN), ("source", self)]
        caster.add_effect(typeclass=DurationEffect, attributes=attributes)
        return True


class Expel(Ability):
    key = "Expel"
    desc = "Collect and expel the negative aura in your body to remove a temporary debuff."

    def at_object_creation(self):
        super().at_object_creation()
        self.db.targeted = False
        self.db.offensive = False
        self.db.range = 0

        self.db.requires = [("wisdom", 5)]
        self.db.ap_cost = 5
        self.db.cost = [("mana", 16)]
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
    desc = "Land your attacks more accurately with a calm and focused mind."

    def at_object_creation(self):
        super().at_object_creation()
        self.db.targeted = False
        self.db.offensive = False
        self.db.range = 0

        self.db.requires = [("wisdom", 2)]
        self.db.ap_cost = 1
        self.db.cost = [("stamina", 5)]
        self.db.cooldown = 5 * SECS_PER_TURN

    def func(self, caster: LivingEntity, target: Object = None):
        caster.location.msg_contents(f"{caster.get_display_name(capital=True)} centers and focuses their mind.")
        attributes = [("effect_key", "+Accuracy"), ("amount", 20), ("duration", 3 * SECS_PER_TURN),
                      ("source", self)]
        caster.add_effect(typeclass=TimedStatMod, attributes=attributes)


class PoisonBlade(Ability):
    key = "Poison Blade"
    desc = "Coat your weapon in poison."

    def at_object_creation(self):
        super().at_object_creation()
        self.db.targeted = False
        self.db.offensive = False
        self.db.range = 0

        self.db.requires = [("intelligence", 4)]
        self.db.ap_cost = 2
        self.db.cost = [("stamina", 8)]
        self.db.cooldown = 8 * SECS_PER_TURN

    def func(self, caster, target=None):
        caster.location.msg_contents(f"{caster.get_display_name(capital=True)} poisons their blade!")
        attributes = [("effect_key", "+Poison Dmg"), ("amount", caster.get_attr("int")),
                      ("duration", 4 * SECS_PER_TURN), ("source", self)]
        caster.add_effect(typeclass=TimedStatMod, attributes=attributes)


class Windstep(Ability):
    key = "Windstep"
    desc = "Move with the wind, greatly increasing your evasion."

    def at_object_creation(self):
        super().at_object_creation()
        self.db.targeted = False
        self.db.offensive = False
        self.db.range = 0

        self.db.requires = [("dexterity", 12)]
        self.db.ap_cost = 6
        self.db.cost = [("stamina", 5)]

        self.db.duration = 5 * SECS_PER_TURN
        self.db.cooldown = 10 * SECS_PER_TURN

    def func(self, caster, target=None):
        caster.location.msg_contents(f"{caster.get_display_name(capital=True)} moves with the wind!")
        attributes = [("effect_key", "+Evasion"), ("amount", caster.get_attr("dex")),  # TODO: Adjust Windstep amount
                      ("duration", self.db.duration), ("source", self)]
        caster.add_effect(typeclass=TimedStatMod, attributes=attributes)

