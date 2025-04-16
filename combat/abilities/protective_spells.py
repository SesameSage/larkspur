from combat.abilities.spells import Spell
from combat.effects import *
from typeclasses.base.objects import Object
from typeclasses.living.living_entities import LivingEntity


class Ward(Spell):
    """Target gains 10 resistance through a protective magical shield."""

    def at_object_creation(self):
        super().at_object_creation()
        self.key = "Ward"
        self.db.targeted = True
        self.db.must_target_entity = True
        self.db.cost = ("mana", 5)

    def cast(self, caster: LivingEntity, target: Object = None):
        if not super().cast(caster, target):
            return False

        caster.location.msg_contents(f"{caster.get_display_name(capital=True)} draws an arc of magical protection"
                                     f"around {target.get_display_name(article=True)}.")

        target.add_effect(TimedStatMod,
                          [("effect_key", "+Resistance"), ("amount", 10), ("duration", 5 * SECS_PER_TURN)])
        return True


class ArmorOfThorns(Spell):
    def at_object_creation(self):
        super().at_object_creation()
        self.key = "Armor of Thorns"
        self.db.targeted = True
        self.db.must_target_entity = True
        self.db.cost = ("mana", 15)

    def cast(self, caster: LivingEntity, target: Object = None):
        if not super().cast(caster, target):
            return False
        attributes = [
            ("effect_key", "Retaliation"),
            ("damage_type", DamageTypes.PIERCING),
            ("amount", 3),
            ("duration", 6 * SECS_PER_TURN)
        ]
        target.add_effect(typeclass=TimedStatMod, attributes=attributes)
        return True
