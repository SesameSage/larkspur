from combat.abilities.spells import Spell
from combat.effects import DurationEffect, SECS_PER_TURN, Frozen
from typeclasses.base.objects import Object
from typeclasses.living.living_entities import LivingEntity


class BlindingBeam(Spell):
    """Causes Blindness, halving target's hitrolls."""

    def at_object_creation(self):
        super().at_object_creation()
        self.key = "Blinding Beam"
        self.db.targeted = True
        self.db.must_target_entity = True
        self.db.cost = ("mana", 5)
        self.db.cooldown = 6 * SECS_PER_TURN

    def cast(self, caster: LivingEntity, target: Object = None):
        if not super().cast(caster, target):
            return False
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

    def cast(self, caster: LivingEntity, target: Object = None):
        if not super().cast(caster=caster, target=target):
            return False

        target.add_effect(Frozen, [("duration", 2 * SECS_PER_TURN)])
        return True
