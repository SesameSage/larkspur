"""Abilities that affect all allies."""

from combat.abilities.abilities import Ability
from combat.combat_handler import COMBAT
from combat.effects import TimedStatMod
from combat.combat_constants import SECS_PER_TURN
from typeclasses.base.objects import Object
from typeclasses.living.living_entities import LivingEntity


class MindClearingTone(Ability):
    key = "Mind-Clearing Tone"
    desc = "This meditational tone improves the accuracy of you and your allies."

    def at_object_creation(self):
        super().at_object_creation()
        self.db.targeted = False
        self.db.offensive = False

        self.db.requires = [("wisdom", 5)]
        self.db.ap_cost = 4
        self.db.cost = [("mana", 12)]
        self.db.cooldown = 5 * SECS_PER_TURN

    def func(self, caster: LivingEntity, target: Object = None):
        # TODO: Sustained spells and abilities
        caster.location.msg_contents(f"{caster.get_display_name(capital=True)} begins a mind-clearing monotonous "
                                     f"hum.")

        attributes = [("effect_key", "+Accuracy"), ("amount", 15), ("duration", 3 * SECS_PER_TURN), ("source", self.key)]
        for ally in COMBAT.get_allies(caster):
                ally.add_effect(typeclass=TimedStatMod, attributes=attributes)


class RallyingCry(Ability):
    key = "Rallying Cry"
    desc = "Rally your allies' morale, giving them additional actions per turn."

    def at_object_creation(self):
        super().at_object_creation()
        self.db.targeted = False
        self.db.offensive = False

        self.db.requires = [("strength", 1), ("wisdom", 1)]
        self.db.ap_cost = 3
        self.db.cost = [("stamina", 5)]
        self.db.cooldown = 10 * SECS_PER_TURN

    def func(self, caster: LivingEntity, target: Object = None):
        caster.location.msg_contents(f"{caster.get_display_name(capital=True)} raises allies' morale with a rallying cry!")
        attributes = [("effect_key", "+AP"), ("amount", 2), ("duration", 2 * SECS_PER_TURN), ("source", self.key)]
        for ally in COMBAT.get_allies(caster):
            ally.add_effect(typeclass=TimedStatMod, attributes=attributes)


class WarCry(Ability):
    key = "War Cry"
    desc = "Your allies hit harder when envigored with your powerful war cry."
    
    def at_object_creation(self):
        super().at_object_creation()
        self.db.targeted = False
        self.db.offensive = False

        self.db.requires = [("strength", 2)]
        self.db.ap_cost = 1
        self.db.cost = [("stamina", 7)]
        self.db.cooldown = 6 * SECS_PER_TURN

    def func(self, caster: LivingEntity, target: Object = None):
        caster.location.msg_contents(f"{caster.get_display_name(capital=True)} lets out an earth-splitting war cry!")
        attributes = [("effect_key", "+Damage"), ("amount", 5), ("duration", 4 * SECS_PER_TURN), ("source", self.key)]
        for ally in COMBAT.get_allies(caster):
            ally.add_effect(typeclass=TimedStatMod, attributes=attributes, stack=True)
