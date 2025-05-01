from combat.abilities.abilities import SpellCompAbility, Ability
from combat.combat_handler import COMBAT
from combat.effects import DamageTypes
from combat.combat_constants import SECS_PER_TURN
from typeclasses.base.objects import Object
from typeclasses.living.living_entities import LivingEntity


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


class PoisonArrow(SpellCompAbility):
    key = "Poison Arrow"
    desc = "Coat an arrow in poison, and take a shot at getting it into the opponent's blood."

    def at_object_creation(self):
        super().at_object_creation()
        self.db.targeted = True
        self.db.must_target_entity = True
        self.db.cooldown = 3 * SECS_PER_TURN

        self.db.requirements = {"poison": 3}
