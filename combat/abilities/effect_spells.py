from combat.abilities.spells import Spell
from combat.effects import DurationEffect, SECS_PER_TURN, Frozen
from typeclasses.base.objects import Object
from typeclasses.living.living_entities import LivingEntity


class BlindingBeam(Spell):
    """Causes Blindness, halving target's hitrolls."""
    key = "Blinding Beam"

    def at_object_creation(self):
        super().at_object_creation()
        self.key = "Blinding Beam"
        self.db.desc = "Blind your target with a focused beam of bright light."
        self.db.targeted = True
        self.db.must_target_entity = True
        self.db.cost = ("mana", 5)
        self.db.cooldown = 6 * SECS_PER_TURN

    def func(self, caster: LivingEntity, target: Object = None):
        caster.location.msg_contents(f"{caster.get_display_name()} aims a focused beam of blinding white light into "
                                     f"{target.get_display_name()}'s eyes!")
        target.add_effect(DurationEffect, [("effect_key", "Blinded"), ("duration", 3 * SECS_PER_TURN)])
        return True


class Freeze(Spell):
    def at_object_creation(self):
        super().at_object_creation()
        self.key = "Freeze"
        self.db.targeted = True
        self.db.must_target_entity = False
        self.db.cost = ("mana", 12)
        self.db.cooldown = 6 * SECS_PER_TURN

    def func(self, caster: LivingEntity, target: Object = None):
        if target.effect_active("Burning"):
            target.scripts.get("Burning").delete()

        target.location.msg_contents(f"{caster.get_display_name(capital=True)} raises nearby water with downturned "
                                     f"fingers, pulls it together to engulf {target.get_display_name(article=True)}, "
                                     f"and separates their hands again in a rapid slicing motion.")

        target.add_effect(Frozen, [("duration", 2 * SECS_PER_TURN)])
        return True
