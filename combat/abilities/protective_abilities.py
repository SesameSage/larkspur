"""Abilities that protect allies."""
from evennia.utils.create import create_script

from combat.abilities.abilities import Ability
from combat.combat_constants import SECS_PER_TURN
from combat.effects import DurationEffect
from typeclasses.base.objects import Object
from typeclasses.living.living_entities import LivingEntity


class Ceasefire(Ability):
    desc = "Prevent all combatants from attacking or using offensive spells."

    def at_object_creation(self):
        super().at_object_creation()
        self.db.targeted = False
        self.db.offensive = False
        self.db.range = None

        self.db.requires = [("wisdom", 4)]
        self.db.ap_cost = 5
        self.db.cost = [("mana", 15)]
        self.db.cooldown = 15 * SECS_PER_TURN

    def func(self, caster: LivingEntity, target: Object = None):
        caster.location.msg_contents(f"{caster.get_display_name(capital=True)} declares a divine ceasefire!")
        # Give dummy longer duration to all other entities in case theirs would tick down first
        attributes = [("effect_key", "Ceasefire"), ("duration", 3 * SECS_PER_TURN), ("source", self)]

        entities = [content for content in caster.location.contents if content.attributes.has("hp")]
        entities.remove(caster)
        for entity in entities:
            entity.add_effect(typeclass=DurationEffect, attributes=attributes)

        # Give actual duration to caster
        attributes.pop(1)
        attributes.append(("duration", 2 * SECS_PER_TURN))
        caster.add_effect(typeclass=DurationEffect, attributes=attributes)
