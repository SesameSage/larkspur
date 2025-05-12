"""Spells cast with a coordinate on the battlefield targeted instead of an object."""
from evennia import create_script

from combat.abilities.spells import TileSpell
from combat.combat_constants import SECS_PER_TURN
from combat.effects import TimedStatMod
from combat.tile_effects import get_tiles, DurationTileEffect, InflictingTile


class AccursedGround(TileSpell):
    key = "Accursed Ground"
    desc = "Damn the land to curse anyone who walks upon it."

    def at_object_creation(self):
        super().at_object_creation()
        self.db.offensive = True
        self.db.range = 8
        self.db.length = 2
        self.db.width = 5
        self.db.duration = 4 * SECS_PER_TURN

        self.db.requires = [("spirit", 6)]
        self.db.ap_cost = 2
        self.db.cost = [("mana", 12)]
        self.db.cooldown = 6 * SECS_PER_TURN

        self.db.tile_color = "|100"
        self.db.script_type = TimedStatMod
        self.db.effect_attributes = [("effect_key", "Cursed"), ("duration", 4 * SECS_PER_TURN), ("source", self)]

    def func(self, caster, target=None):
        caster.location.msg(f"{caster.get_display_name(capital=True)} calls insects to swarm the battlefield!")

        effect_attributes = self.db.effect_attributes
        effect_attributes.append(("amount", caster.get_attr("spirit")))
        effect_attributes.append(("duration", 4 * SECS_PER_TURN))

        attributes = self.db.attributes
        attributes.append(
            ("tiles", get_tiles(entity=caster, center=target, length=self.db.length, width=self.db.width)))
        attributes.append(("script_type", self.db.script_type))
        attributes.append(("effect_attributes", effect_attributes))

        grid = caster.db.combat_turnhandler.db.grid
        script = create_script(typeclass=InflictingTile, key=self.key, obj=caster, attributes=attributes)
        script.pre_effect_add()
        grid.db.effects.append(script)



