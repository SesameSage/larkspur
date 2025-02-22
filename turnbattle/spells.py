from turnbattle.abilities import *


class Spell(Ability):
    pass


class SustainedSpell(SustainedAbility, Spell):
    pass


class Firebolt(Spell):
    def at_object_creation(self):
        super().at_object_creation()
        self.db.targeted = True
        self.db.must_target_entity = False
        self.db.cost = {"mana": 2}
        self.db.cooldown = 3

    def cast(self, caster: LivingEntity, target: Object = None):
        if not super().cast(caster=caster, target=target):
            return False
        damage_mod = caster.db.mods["fire damage"] if "fire damage" in caster.db.mods else 1
        fire_damage = caster.get_attr(CharAttrib.SPIRIT) * damage_mod
        ignite_buildup = 0

        if not hasattr(target, "rules") or not target.rules.is_in_combat(target):
            caster.execute_cmd("fight")
        target.apply_damage({DamageTypes.FIRE: fire_damage})

        target.scripts.add(DamageOverTime(effect_key="Burning", range=(1, 1),
                                          duration=Dec(10), damage_type=DamageTypes.FIRE))
        return True

