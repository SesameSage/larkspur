from server.appearance import dmg_color
from turnbattle.abilities import *


class Spell(Ability):
    def get_display_name(self, looker=None, capital=False, **kwargs):
        return appearance.spell + self.name


class SustainedSpell(SustainedAbility, Spell):
    pass


class Firebolt(Spell):
    """Causes fire damage and inflicts Burning, adding more damage over time."""

    def at_object_creation(self):
        super().at_object_creation()
        self.db.targeted = True
        self.db.must_target_entity = False
        self.db.cost = ("mana", 2)
        self.db.cooldown = 2 * SECS_PER_TURN

    def cast(self, caster: LivingEntity, target: Object = None):
        if not super().cast(caster=caster, target=target):
            return False

        damage_mod = caster.db.mods["fire damage"] if "fire damage" in caster.db.mods else 1
        fire_damage = caster.get_attr("spirit") * damage_mod
        caster.location.more_info(f"{fire_damage} fire damage = "
                                  f"{caster.get_attr("spirit")} Spirit * {damage_mod} mod")
        ignite_buildup = 0

        if not target.is_in_combat():
            caster.execute_cmd("fight")
        target.apply_damage({DamageTypes.FIRE: fire_damage})
        caster.location.msg_contents(f"A bolt of fire ignites in {caster.get_display_name()}'s hand and scorches "
                                     f"{target.get_display_name()} for {dmg_color(caster, target)}{fire_damage} fire damage!")

        target.add_effect(Burning,
                          [("range", (1, 1)), ("duration", 3 * SECS_PER_TURN)])
        return True


class BlindingBeam(Spell):
    """Causes Blindness, halving target's hitrolls."""

    def at_object_creation(self):
        super().at_object_creation()
        self.db.targeted = True
        self.db.must_target_entity = True
        self.db.cost = ("mana", 5)

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
        self.db.targeted = True
        self.db.must_target_entity = False
        self.db.cost = ("mana", 12)
        self.db.cooldown = 6 * SECS_PER_TURN

    def cast(self, caster: LivingEntity, target: Object = None):
        if not super().cast(caster=caster, target=target):
            return False

        target.add_effect(Frozen, [("duration", 2 * SECS_PER_TURN)])
        return True