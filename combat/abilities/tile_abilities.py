"""Abilities cast with a coordinate on the battlefield targeted instead of an object."""
from evennia.utils.create import create_script

from combat.abilities.abilities import TileAbility
from combat.combat_constants import SECS_PER_TURN
from combat.tile_effects import DurationTileEffect, get_tiles


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
        attributes.append(("tiles", get_tiles(entity=caster, center=target, length=self.db.length, width=self.db.width)))

        grid = caster.db.combat_turnhandler.db.grid
        script = create_script(typeclass=DurationTileEffect, key=self.key, obj=caster, attributes=self.db.attributes)
        script.pre_effect_add()
        grid.db.effects.append(script)
