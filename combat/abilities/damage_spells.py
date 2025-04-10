from combat.abilities.spells import Spell
from combat.effects import SECS_PER_TURN, DamageTypes, Burning
from server.appearance import dmg_color
from typeclasses.base.objects import Object
from typeclasses.living.living_entities import LivingEntity


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
