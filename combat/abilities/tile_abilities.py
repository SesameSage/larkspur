"""Abilities cast with a coordinate on the battlefield targeted instead of an object."""
from evennia.utils.create import create_script

from combat.abilities.abilities import TileAbility
from combat.combat_constants import SECS_PER_TURN
from combat.effects import DamageTypes
from combat.tile_effects import DurationTileEffect, get_tiles, TileDamage


class Swarm(TileAbility):
    desc = ("Call insects to swarm on the battlefield, preventing anyone caught in the swarm from attacking or using "
            "abilities.")

    def at_object_creation(self):
        super().at_object_creation()
        self.db.offensive = True
        self.db.range = 5
        self.db.length = 3
        self.db.width = 3
        self.db.duration = 5 * SECS_PER_TURN

        self.db.requires = [("intelligence", 3)]
        self.db.ap_cost = 2
        self.db.cost = [("mana", 6)]
        self.db.cooldown = 5 * SECS_PER_TURN

        self.db.tile_color = "|210"

    def func(self, caster, target=None):
        caster.location.msg(f"{caster.get_display_name(capital=True)} calls insects to swarm the battlefield!")

        attributes = self.db.attributes
        attributes.append(
            ("tiles", get_tiles(entity=caster, center=target, length=self.db.length, width=self.db.width)))

        grid = caster.db.combat_turnhandler.db.grid
        script = create_script(typeclass=DurationTileEffect, key=self.key, obj=caster, attributes=self.db.attributes)
        script.pre_effect_add()
        grid.db.effects.append(script)


class Thistle(TileAbility):
    desc = "Cover the ground in thistles to damage anyone stepping through."

    def at_object_creation(self):
        super().at_object_creation()
        self.db.offensive = True

        self.db.range = 6
        self.db.length = 2
        self.db.width = 5
        self.db.duration = 10 * SECS_PER_TURN

        self.db.damage_type = DamageTypes.PIERCING
        self.db.dmg_range = (5, 7)

        self.db.requires = [("intelligence", 1)]
        self.db.ap_cost = 1
        self.db.cost = [("stamina", 3)]
        self.db.cooldown = 5 * SECS_PER_TURN

        self.db.tile_color = "|010"

    def func(self, caster, target=None):
        # TODO: DRY the reused at-cast code for tile abilities
        caster.location.msg(f"{caster.get_display_name(capital=True)} covers the ground in sharp thistles!")

        unique_attributes = [
            ("tiles", get_tiles(entity=caster, center=target, length=self.db.length, width=self.db.width)),
            ("damage_type", self.db.damage_type), ("range", self.db.dmg_range)
        ]
        attributes = self.db.attributes + unique_attributes

        grid = caster.db.combat_turnhandler.db.grid
        script = create_script(typeclass=TileDamage, key=self.key, obj=caster, attributes=attributes)
        script.pre_effect_add()
        grid.db.effects.append(script)

