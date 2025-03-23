from server.appearance import dmg_color
from turnbattle.abilities import *


class Spell(Ability):
    def get_display_name(self, looker=None, capital=False, **kwargs):
        return appearance.spell + self.name


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

        if not target.is_in_combat():
            caster.execute_cmd("fight")
        target.apply_damage({DamageTypes.FIRE: fire_damage})
        caster.location.msg_contents(f"A bolt of fire ignites in {caster.get_display_name()}'s hand and scorches "
                                     f"{target.get_display_name()} for {dmg_color(caster, target)}{fire_damage} fire damage!")

        target.add_effect(DamageOverTime, [("effect_key", "Burning"), ("range", (1, 1)), ("duration", 15), ("damage_type", 4)])
        return True
