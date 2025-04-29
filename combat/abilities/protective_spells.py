from combat.abilities.spells import Spell
from combat.effects import *
from typeclasses.base.objects import Object
from typeclasses.living.living_entities import LivingEntity


class Ward(Spell):
    """Target gains 10 resistance through a protective magical shield."""
    desc = "Protect a target with a magical shield of resistance."

    def at_object_creation(self):
        super().at_object_creation()
        self.db.targeted = True
        self.db.must_target_entity = True
        self.db.offensive = False

        self.db.requires = [("wisdom", 6)]
        self.db.cost = [("mana", 5)]
        self.db.cooldown = 3 * SECS_PER_TURN

    def func(self, caster: LivingEntity, target: Object = None):
        caster.location.msg_contents(f"{caster.get_display_name(capital=True)} draws an arc of magical protection "
                                     f"around {target.get_display_name(article=True)}.")

        target.add_effect(TimedStatMod,
                          [("effect_key", "+Resistance"), ("amount", 10), ("duration", 5 * SECS_PER_TURN)])
        return True


class ArmorOfThorns(Spell):
    key = "Armor of Thorns"
    desc = "Protect your target with a coat of thorns to damage melee attackers."

    def at_object_creation(self):
        super().at_object_creation()
        self.db.targeted = True
        self.db.must_target_entity = True
        self.db.offensive = False

        self.db.requires = [("wisdom", 2)]
        self.db.cost = [("mana", 8)]
        self.db.cooldown = 3 * SECS_PER_TURN

    def func(self, caster: LivingEntity, target: Object = None):
        attributes = [
            ("effect_key", "Retaliation"),
            ("damage_type", DamageTypes.PIERCING),
            ("amount", 3),
            ("duration", 6 * SECS_PER_TURN)
        ]
        target.add_effect(typeclass=TimedStatMod, attributes=attributes)
        return True


class ThermalSink(Spell):
    """+10 Fire and Cold resistance"""
    key = "Thermal Sink"
    desc = "Enshroud an ally with a heat sink capable of insulating both hot and cold damage."

    def at_object_creation(self):
        super().at_object_creation()
        self.db.targeted = True
        self.db.must_target_entity = False
        self.db.offensive = False

        self.db.requires = [("wisdom", 3)]
        self.db.cost = [("mana", 15)]

    def func(self, caster: LivingEntity, target: Object = None):
        attributes = [
            ("amount", 10),
            ("duration", 6 * SECS_PER_TURN)
        ]
        fire_attributes = attributes + [
            ("effect_key", "+Fire Resist"),
            ("damage_type", DamageTypes.FIRE)]
        cold_attributes = attributes + [
            ("effect_key", "+Cold Resist"),
            ("damage_type", DamageTypes.COLD)]
        target.add_effect(typeclass=TimedStatMod, attributes=fire_attributes)
        target.add_effect(typeclass=TimedStatMod, attributes=cold_attributes)

        return True
