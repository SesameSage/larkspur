from combat.abilities.spells import Spell
from combat.combat_handler import COMBAT
from combat.effects import DamageTypes, Burning
from combat.combat_constants import SECS_PER_TURN
from server.appearance import dmg_color
from typeclasses.base.objects import Object
from typeclasses.living.living_entities import LivingEntity


class Firebolt(Spell):
    """Causes fire damage and inflicts Burning, adding more damage over time."""
    desc = "Ignite a bolt of fire and hurl it towards your target for a chance to ignite."

    def at_object_creation(self):
        super().at_object_creation()
        self.db.targeted = True
        self.db.must_target_entity = False

        self.db.requires = [("spirit", 2)]
        self.db.ap_cost = 2
        self.db.cost = [("mana", 2)]
        self.db.cooldown = 2 * SECS_PER_TURN

    def get_damage(self, caster):
        damage_mod = caster.db.mods["fire damage"] if "fire damage" in caster.db.mods else 1
        fire_damage = caster.get_attr("spirit") * damage_mod
        caster.location.more_info(f"{fire_damage} fire damage = "
                                  f"{caster.get_attr("spirit")} Spirit * {damage_mod} mod")
        return {DamageTypes.FIRE: fire_damage}

    def func(self, caster: LivingEntity, target: Object = None):
        ignite_buildup = 0

        if not target.is_in_combat():
            caster.execute_cmd("fight")

        announce_msg = (f"A bolt of fire ignites in {caster.get_display_name()}'s hand and scorches "
                        f"{target.get_display_name()} for ")
        hit_result, damage_values = COMBAT.resolve_attack(attacker=caster, defender=target, attack=self,
                                                          announce_msg=announce_msg)
        if hit_result and DamageTypes.FIRE in damage_values and damage_values[DamageTypes.FIRE] > 0:
            # Inflict burning only if the fire damage is not fully resisted
            # TODO: Should immunity to effects be separate?
            target.add_effect(Burning,
                              [("range", (1, 1)), ("duration", 3 * SECS_PER_TURN)])
        return True
