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
        caster.location.more_info(f"{fire_damage} fire damage = "
                                  f"{caster.get_attr(CharAttrib.SPIRIT)} Spirit * {damage_mod} mod")
        ignite_buildup = 0

        if not hasattr(target, "rules") or not target.rules.is_in_combat(target):
            caster.execute_cmd("fight")
        target.apply_damage({DamageTypes.FIRE: fire_damage})
        caster.location.msg_contents(f"A bolt of fire ignites in {caster.get_display_name()}'s hand and scorches "
                                     f"{target.get_display_name()} for {fire_damage} fire damage!")

        if "Burning" not in target.db.effects:
            target.scripts.add(DamageOverTime(effect_key="Burning", range=(1, 1),
                                              duration=Dec(10), damage_type=DamageTypes.FIRE))
            caster.location.msg_contents(f"{target.get_display_name()} ignites and begins to burn!")
        else:
            target.scripts.get("DamageOverTime")[0].db.seconds_passed = 0

            caster.location.msg_contents(f"The fire on {target.get_display_name()} reignites!")
        return True
