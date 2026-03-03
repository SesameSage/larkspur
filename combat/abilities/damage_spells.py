"""Spells focused on dealing damage."""
from random import randint

from evennia.utils import inherits_from

from combat.abilities.spells import Spell
from combat.combat_constants import SECS_PER_TURN, DamageTypes
from combat.combat_handler import COMBAT
from combat.effects import Burning
from server import appearance
from typeclasses.base.objects import Object
from typeclasses.living.living_entities import LivingEntity


class Firebolt(Spell):
    """Causes fire damage and inflicts Burning, adding more damage over time."""
    key = "Firebolt"
    desc = "Ignite a bolt of fire and hurl it towards your target for a chance to ignite."

    def at_object_creation(self):
        super().at_object_creation()
        self.db.targeted = True
        self.db.must_target_entity = False
        self.db.range = 5

        self.db.requires = [("spirit", 2)]
        self.db.ap_cost = 2
        self.db.cost = [("mana", 3)]
        self.db.cooldown = 2 * SECS_PER_TURN

    def get_damage(self, caster):
        fire_damage = caster.get_attr("spirit")
        return {DamageTypes.FIRE: fire_damage}

    def func(self, caster: LivingEntity, target: Object = None):
        announce_msg = (f"A bolt of fire ignites in {caster.get_display_name()}'s hand and scorches "
                        f"{target.get_display_name()} for ")
        hit_result, damage_values = COMBAT.resolve_attack(attacker=caster, defender=target, attack=self,
                                                          announce_msg=announce_msg)
        if hit_result and DamageTypes.FIRE in damage_values and damage_values[DamageTypes.FIRE] > 0:
            # Inflict burning only if the fire damage is not fully resisted
            # TODO: Should immunity to effects be separate?
            if randint(1,100) + (2 * caster.get_attr("spirit")) > 80: # 20% chance to burn + spirit bonus
                target.add_effect(Burning,
                                  [("range", (1, 1)), ("duration", 3 * SECS_PER_TURN)])


class LightningBolt(Spell):
    key = "Lightning Bolt"
    desc = "Shoot a bolt of lightning straight out, shocking anything in its path."

    def at_object_creation(self):
        super().at_object_creation()
        self.db.targeted = True
        self.db.must_target_entity = False
        self.db.range = 8
        self.db.targets_tile = True

        self.db.requires = [("spirit", 3)]
        self.db.ap_cost = 3
        self.db.cost = [("mana", 4)]

    def get_damage(self, caster):
        shock_damage = caster.get_attr("spirit")
        return {DamageTypes.SHOCK: shock_damage}

    def func(self, caster: LivingEntity, target: Object = None):
        caster.location.msg_contents(f"Lightning shoots out from {caster.get_display_name()}'s hands!")
        spell_damage = self.get_damage(caster)
        grid = caster.db.combat_turnhandler.db.grid
        direction = grid.direction_to(caster, target)

        for i in range(1, 8):
            occupant = 0
            occupant = grid.check_square(direction=direction, obj=caster,     distance=i)
            if occupant and inherits_from(occupant, "stats.combat_character.CombatEntity"):
                damage_taken = COMBAT.get_damage_taken(defender=occupant, damage_values=spell_damage)
                occupant.apply_damage(damage_taken)
                occupant.location.msg_contents(f"{occupant.get_display_name(capital=True)} is struck by lightning for "
                                               f"{appearance.dmg_color(occupant)}{damage_taken[DamageTypes.SHOCK]} damage|n!")


class Smite(Spell):
    """Deals magic damage."""
    key = "Smite"
    desc = "Call on the gods to strike your foe."

    def at_object_creation(self):
        super().at_object_creation()
        self.db.targeted = True
        self.db.must_target_entity = False
        self.db.range = 8

        self.db.requires = [("spirit", 1)]
        self.db.ap_cost = 2
        self.db.cost = [("mana", 3)]
        self.db.cooldown = 2 * SECS_PER_TURN

    def get_damage(self, caster):
        return {DamageTypes.ARCANE: caster.get_attr("spirit")}

    def func(self, caster: LivingEntity, target: Object = None):
        announce_msg = f"{caster.get_display_name()} prays, and an unseen force strikes {target.get_display_name()}!"
        COMBAT.resolve_attack(caster, target, self, announce_msg)


class WaterWhip(Spell):
    """If water of some kind is found in the room, uses it to damage opponents."""
    key = "Water Whip"
    desc = "Pull nearby water into a stream to whip your opponent."

    def at_object_creation(self):
        super().at_object_creation()
        self.db.targeted = True
        self.db.must_target_entity = False
        self.db.range = 3

        self.db.requires = [("spirit", 2)]
        self.db.ap_cost = 2
        self.db.cost = [("mana", 2)]
        self.db.cooldown = 2 * SECS_PER_TURN

    def check(self, caster, target):
        if not super().check(caster, target):
            return False
        if not caster.location.has_water():
            caster.msg("There's no water here!")
            return False
        return True

    def get_damage(self, caster):
        return {None: caster.get_attr("spirit") * 2}

    def func(self, caster: LivingEntity, target: Object = None):
        caster.location.msg_contents(f"{caster.get_display_name(capital=True)} whips {target.get_display_name()} with "
                                     f"nearby water!")
        COMBAT.resolve_attack(attacker=caster, defender=target, attack=self)
