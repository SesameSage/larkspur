from combat.abilities.abilities import SpellCompAbility, Ability
from combat.combat_handler import COMBAT
from combat.effects import SECS_PER_TURN, DamageTypes
from typeclasses.base.objects import Object
from typeclasses.living.living_entities import LivingEntity


class Scratch(Ability):
    def at_object_creation(self):
        super().at_object_creation()
        self.db.targeted = True
        self.db.must_target_entity = False
        self.db.cost = ("stamina", 1)
        self.db.cooldown = 0

    def get_damage(self, caster):
        damage = 5 + caster.get_attr("str")
        return {DamageTypes.SLASHING: damage}

    def func(self, caster: LivingEntity, target: Object = None):
        COMBAT.resolve_attack(caster, target, self)
        return True


class PoisonArrow(SpellCompAbility):
    key = "Poison Arrow"
    def at_object_creation(self):
        super().at_object_creation()
        self.db.targeted = True
        self.db.must_target_entity = True
        self.db.cooldown = 3 * SECS_PER_TURN

        self.db.requirements = {"poison": 3}
