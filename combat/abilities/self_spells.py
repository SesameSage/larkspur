from combat.abilities.spells import Spell
from combat.effects import SECS_PER_TURN, DurationEffect
from typeclasses.base.objects import Object
from typeclasses.living.living_entities import LivingEntity


class Consume(Spell):
    def at_object_creation(self):
        self.db.desc = "Leech life into your own body as you ravage your opponents."
        self.db.targeted = False

        self.db.requires = [("spirit", 7)]
        self.db.cost = [("mana", 12)]
        self.db.cooldown = 8 * SECS_PER_TURN

    def func(self, caster: LivingEntity, target: Object = None):
        caster.location.msg_contents(f"{caster.get_display_name(capital=True)} begins grotesquely consuming life from "
                                     f"their foes!")
        attributes = [("effect_key", "Siphon HP"), ("duration", 5 * SECS_PER_TURN), ("positive", True)]
        caster.add_effect(typeclass=DurationEffect, attributes=attributes)
        return True


class AbsorbEssence(Spell):
    key = "Absorb Essence"

    def at_object_creation(self):
        super().at_object_creation()
        self.db.desc = "Drain your opponents' mana into your own as you deal damage."
        self.db.targeted = False

        self.db.requires = [("spirit", 9)]
        self.db.cost = [("mana", 8)]
        self.db.cooldown = 8 * SECS_PER_TURN

    def func(self, caster: LivingEntity, target: Object = None):
        caster.location.msg_contents(f"{caster.get_display_name(capital=True)} creates an inward flow of mental "
                                     f"energy, absorbing mana from their enemies!")
        attributes = [("effect_key", "Siphon Mana"), ("duration", 5 * SECS_PER_TURN), ("positive", True)]
        caster.add_effect(typeclass=DurationEffect, attributes=attributes)
        return True
