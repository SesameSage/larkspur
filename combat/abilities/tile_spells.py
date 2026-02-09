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
        self.db.effect_attributes = [("effect_key", "Cursed"), ("duration", 4 * SECS_PER_TURN),
                                     ("source", self.get_display_name())]

    def func(self, caster, target=None):
        caster.location.msg(f"{caster.get_display_name(capital=True)} lays a curse upon the ground!")

        effect_attributes = self.db.effect_attributes
        effect_attributes.append(("amount", caster.get_attr("spirit")))
        effect_attributes.append(("duration", 4 * SECS_PER_TURN))

        attributes = self.db.attributes
        attributes.append(
            ("tiles", get_tiles(entity=caster, center=target, length=self.db.length, width=self.db.width)))
        attributes.append(("script_type", self.db.script_type))
        attributes.append(("effect_attributes", effect_attributes))

        grid = caster.db.combat_turnhandler.db.grid
        # TODO: Nonetype create_script
        script = create_script(typeclass=InflictingTile, key=self.key, obj=caster, attributes=attributes)
        script.pre_effect_add()
        grid.db.effects.append(script)


class GravityField(TileSpell):
    key = "Gravity Field"
    desc = "Create a high-gravity bubble that hinders strength."

    def at_object_creation(self):
        super().at_object_creation()
        self.db.offensive = True
        self.db.range = 5
        self.db.length = 4
        self.db.width = 4
        self.db.duration = 5 * SECS_PER_TURN

        self.db.requires = [("spirit", 3)]
        self.db.ap_cost = 2
        self.db.cost = [("mana", 12)]
        self.db.cooldown = 8 * SECS_PER_TURN

        self.db.tile_color = "|511"

    def func(self, caster, target=None):
        caster.location.msg_contents(f"{caster.get_display_name(capital=True)} creates a burdening gravity field to "
                                     f"weaken strength!")

        attributes = self.db.attributes
        attributes.append(
            ("tiles", get_tiles(entity=caster, center=target, length=self.db.length, width=self.db.width)))
        attributes.remove(("effect_key", self.key))
        attributes.append(("effect_key", "-Strength"))
        attributes.append(("amount", caster.get_attr("spirit")))

        grid = caster.db.combat_turnhandler.db.grid
        script = create_script(typeclass=DurationTileEffect, key=self.key, obj=caster, attributes=attributes)
        script.pre_effect_add()
        grid.db.effects.append(script)





class SuppressionField(TileSpell):
    key = "Suppression Field"
    desc = "Prevent magic spells from being cast in a target area."

    def at_object_creation(self):
        super().at_object_creation()
        self.db.offensive = True
        self.db.range = 5
        self.db.length = 3
        self.db.width = 4
        self.db.duration = 5 * SECS_PER_TURN

        self.db.requires = [("wisdom", 3)]
        self.db.ap_cost = 2
        self.db.cost = [("mana", 15)]
        self.db.cooldown = 8 * SECS_PER_TURN

        self.db.tile_color = "|143"

    def func(self, caster, target=None):
        caster.location.msg(f"{caster.get_display_name(capital=True)} draws a magic suppression field!")

        attributes = self.db.attributes
        attributes.append(
            ("tiles", get_tiles(entity=caster, center=target, length=self.db.length, width=self.db.width)))
        attributes.remove(("effect_key", self.key))
        attributes.append(("effect_key", "Magic Suppression"))

        grid = caster.db.combat_turnhandler.db.grid
        script = create_script(typeclass=DurationTileEffect, key=self.key, obj=caster, attributes=attributes)
        script.pre_effect_add()
        grid.db.effects.append(script)
