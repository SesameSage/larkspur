"""Abilities focused on inflicting effects."""

from random import randint

from combat.abilities.abilities import Ability
from combat.combat_handler import COMBAT
from combat.effects import KnockedDown, TimedStatMod, DurationEffect
from combat.combat_constants import SECS_PER_TURN
from typeclasses.base.objects import Object
from typeclasses.living.living_entities import LivingEntity


class KneeSlash(Ability):
    key = "Knee Slash"
    desc = "Cripple your opponent, slowing their movement."

    def at_object_creation(self):
        super().at_object_creation()
        self.db.targeted = True
        self.db.must_target_entity = True
        self.db.range = 1

        self.db.requires = [("dexterity", 1)]
        self.db.ap_cost = 1
        self.db.cost = [("stamina", 2)]
        self.db.cooldown = 8 * SECS_PER_TURN

    def func(self, caster, target=None):
        caster.location.msg_contents(f"{caster.get_display_name(capital=True)} lacerates "
                                     f"{target.get_display_name(article=True)}'s knee!")

        attributes = [("effect_key", "Slowed"), ("duration", 4 * SECS_PER_TURN), ("source", self)]
        target.add_effect(typeclass=DurationEffect, attributes=attributes)


class NeutralizingHum(Ability):
    key = "Neutralizing Hum"
    desc = "Drain mana from all nearby opponents with this throat-singing tone."

    def at_object_creation(self):
        super().at_object_creation()
        self.db.targeted = False
        self.db.range = 5

        self.db.requires = [("wisdom", 8)]
        self.db.ap_cost = 5
        self.db.cost = [("mana", 10)]
        self.db.cooldown = 10 * SECS_PER_TURN

    def func(self, caster: LivingEntity, target: Object = None):
        caster.location.msg_contents(
            f"{caster.get_display_name(capital=True)} emits a low, guttural throat-singing tone.")

        for entity in COMBAT.get_enemies(caster):
            if entity.get_resistance(None) < 20:
                entity.db.mana -= 25
                if entity.db.mana < 0:
                    entity.db.mana = 0
                entity.location.msg_contents(f"{entity.get_display_name(capital=True)}'s mana has been drained!")
            else:
                entity.location.msg_contents(
                    f"{entity.get_display_name(capital=True)} resists {self.get_display_name()}!")

        return True


class SolarPlexusStrike(Ability):
    key = "Solar Plexus Strike"
    desc = ("Strike at the center of power in the body, weakening your opponent's attack and potentially "
            "winding them.")

    def at_object_creation(self):
        super().at_object_creation()
        self.db.targeted = True
        self.db.must_target_entity = True
        self.db.range = 1

        self.db.requires = [("dexterity", 10)]
        self.db.ap_cost = 5
        self.db.cost = [("stamina", 10)]
        self.db.cooldown = 5 * SECS_PER_TURN

    def func(self, caster: LivingEntity, target: Object = None):
        if target.get_attr("constitution") > caster.get_attr("dexterity") * 2:
            caster.location.msg_contents(f"{target.get_display_name(capital=True)} is too hardened for "
                                         f"{caster.get_display_name()}'s {self.get_display_name()}!")
            return True

        target.location.msg_contents(f"{caster.get_display_name(capital=True)} strikes at the center of power in "
                                     f"{target.get_display_name()}'s body!")
        attributes = [("effect_key", "-Damage"), ("amount", -5), ("duration", 4 * SECS_PER_TURN), ("source", self)]
        target.add_effect(typeclass=TimedStatMod, stack=True, attributes=attributes)

        if target.get_attr("con") < 1.25 * caster.get_attr("dex"):
            if randint(1, 3) > 1:
                attributes = [("effect_key", "Winded"), ("duration", 3 * SECS_PER_TURN), ("source", self)]
                target.add_effect(typeclass=DurationEffect, attributes=attributes)


class Sweep(Ability):
    """Attempts to knock an opponent down."""
    key = "Sweep"
    desc = "Sweep your weapon underneath an opponent's legs, attempting to knock them off their feet."

    def at_object_creation(self):
        super().at_object_creation()

        self.db.targeted = True
        self.db.must_target_entity = True
        self.db.range = 1

        self.db.requires = [("dexterity", 2)]

        self.db.ap_cost = 3
        self.db.cost = [("stamina", 1)]
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
            target.location.msg_contents(
                f"{caster.get_display_name(capital=True)} sweeps at {target.get_display_name()}'s legs, "
                f"knocking them to the ground!")
            target.add_effect(KnockedDown, attributes=[("source", self)])
        return True
