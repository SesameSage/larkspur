"""Abilities focused on inflicting effects."""

from random import randint

from combat.abilities.abilities import Ability
from combat.combat_handler import COMBAT
from combat.effects import KnockedDown, StatMod, TimedStatMod, DurationEffect, DamageTypes
from combat.combat_constants import SECS_PER_TURN
from typeclasses.base.objects import Object
from typeclasses.inanimate.items.equipment.apparel import Shield
from typeclasses.living.living_entities import LivingEntity


class NeutralizingHum(Ability):
    key = "Neutralizing Hum"
    desc = "Drain mana from all opponents with this throat-singing tone."

    def at_object_creation(self):
        super().at_object_creation()
        self.db.targeted = False

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


class ShieldBash(Ability):
    key = "Shield Bash"
    desc = "Attempt to knock your opponent to the ground with your shield."

    def at_object_creation(self):
        super().at_object_creation()

        self.db.targeted = True
        self.db.must_target_entity = False

        self.db.requires = [("strength", 4)]

        self.db.ap_cost = 3
        self.db.cost = [("stamina", 20)]
        self.db.cooldown = 6 * SECS_PER_TURN

    def check(self, caster, target):
        if not super().check(caster, target):
            return False

        if not isinstance(caster.db.equipment["secondary"], Shield):  # If caster doesn't have a shield equipped
            caster.msg("You don't have a shield equipped!")
            return False
        return True

    def func(self, caster: LivingEntity, target: Object = None):
        caster.location.msg_contents(f"{caster.get_display_name(capital=True)} uses their shield to charge at "
                                     f"{target.get_display_name(article=True)} with the full weight of their body!")

        strength_factor = caster.get_attr("str")
        shield_factor = caster.db.equipment["secondary"].db.defense[None]
        knockdown_power = strength_factor + shield_factor

        damage = shield_factor
        COMBAT.resolve_attack(attacker=caster, defender=target, attack=self, damage_values={DamageTypes.BLUNT: damage})

        knockdown_resistance = target.get_attr("constitution") + randint(1, 3)
        if knockdown_resistance > knockdown_power:
            caster.location.msg_contents(f"{target.get_display_name(capital=True)} stands strong!")
        else:
            target.add_effect(KnockedDown, attributes=[("source", self.key)])


class SolarPlexusStrike(Ability):
    key = "Solar Plexus Strike"
    desc = ("Strike at the center of power in the body, weakening your opponent's attack and potentially "
            "winding them.")

    def at_object_creation(self):
        super().at_object_creation()
        self.db.targeted = True
        self.db.must_target_entity = True

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
        attributes = [("effect_key", "-Damage"), ("amount", -5), ("duration", 4 * SECS_PER_TURN)]
        target.add_effect(typeclass=TimedStatMod, stack=True, attributes=attributes)

        if target.get_attr("con") < 1.25 * caster.get_attr("dex"):
            if randint(1, 3) > 1:
                attributes = [("effect_key", "Winded"), ("duration", 3 * SECS_PER_TURN), ("source", self.key)]
                target.add_effect(typeclass=DurationEffect, attributes=attributes)


class Sweep(Ability):
    """Attempts to knock an opponent down."""
    desc = "Sweep your weapon underneath an opponent's legs, attempting to knock them off their feet."

    def at_object_creation(self):
        super().at_object_creation()

        self.db.targeted = True
        self.db.must_target_entity = True

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
            target.location.msg_contents(f"{caster.get_display_name(capital=True)} sweeps at {target.get_display_name()}'s legs, "
                                         f"knocking them to the ground!")
            target.add_effect(KnockedDown, attributes=[("source", self.key)])
        return True
