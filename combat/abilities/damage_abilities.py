"""Abilities focused on dealing damage."""
from random import randint

from combat.abilities.abilities import Ability, BowAbility
from combat.combat_handler import COMBAT
from combat.effects import DamageTypes, KnockedDown, Poisoned
from combat.combat_constants import SECS_PER_TURN
from typeclasses.base.objects import Object
from typeclasses.inanimate.items.equipment.apparel import Shield
from typeclasses.living.living_entities import LivingEntity


class FocusedShot(BowAbility):
    key = "Focused Shot"
    desc = ("Concentrate deeply on your aim and the enemy's movements to help your arrow find even the most evasive of "
            "targets.")

    def at_object_creation(self):
        super().at_object_creation()
        self.db.targeted = True
        self.db.must_target_entity = False

        self.db.cost = [("stamina", 10)]
        self.db.ap_cost = 5
        self.db.cooldown = 3 * SECS_PER_TURN

    def get_damage(self, caster):
        return COMBAT.get_weapon_damage(caster)

    def func(self, caster: LivingEntity, target: Object = None):
        COMBAT.resolve_attack(attacker=caster, defender=target, attack=self,
                              accuracy=COMBAT.get_accuracy(caster, target) + 30)


class PoisonArrow(Ability):
    key = "Poison Arrow"
    desc = "Coat an arrow in poison, and take a shot at getting it into the opponent's blood."

    def at_object_creation(self):
        super().at_object_creation()
        self.db.targeted = True
        self.db.must_target_entity = True

        self.db.cost = [("stamina", 3)]
        self.db.ap_cost = 3
        self.db.cooldown = 5 * SECS_PER_TURN

    def get_damage(self, caster):
        damage_values = COMBAT.get_weapon_damage(caster)
        damage_values[DamageTypes.POISON] = 5
        return damage_values

    def func(self, caster: LivingEntity, target: Object = None):
        hit_result, damage_values = COMBAT.resolve_attack(attacker=caster, defender=target, attack=self)
        if hit_result and DamageTypes.POISON in damage_values and damage_values[DamageTypes.POISON] > 0:
            # Inflict poisoning only if the poison damage is not fully resisted
            target.add_effect(Poisoned,
                              [("range", (1, 3)), ("duration", 3 * SECS_PER_TURN)])


class Scratch(Ability):
    desc = "Scratch your opponent with claws, talons, etc."

    def at_object_creation(self):
        super().at_object_creation()
        self.db.targeted = True
        self.db.must_target_entity = False

        self.db.cost = [("stamina", 1)]
        self.db.ap_cost = 2
        self.db.cooldown = 0

    def get_damage(self, caster):
        damage = 5 + caster.get_attr("str")
        return {DamageTypes.SLASHING: damage}

    def func(self, caster: LivingEntity, target: Object = None):
        COMBAT.resolve_attack(caster, target, self)
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
