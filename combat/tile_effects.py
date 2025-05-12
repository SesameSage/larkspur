from random import randint

from combat.effects import EffectScript, DurationEffect
from server import appearance


def get_tiles(entity, center: tuple, length, width):
    def orient_to_entity():
        delta_x = center[0] - entity.db.combat_x
        delta_y = center[1] - entity.db.combat_y

        abs_delta_x = abs(delta_x)
        abs_delta_y = abs(delta_y)

        if abs_delta_y >= abs_delta_x:
            # Caster is mostly north/south of target tile
            x_tiles = width
            y_tiles = length
        else:
            # Caster is mostly east/west of target tile
            x_tiles = length
            y_tiles = width
        return x_tiles, y_tiles

    # Single tile effects
    if width == 1 and length == 1:
        return [center]

    center_x = center[0]
    center_y = center[1]
    x_tiles, y_tiles = orient_to_entity()

    west_reach = x_tiles // 2
    east_reach = (x_tiles - 1) // 2
    north_reach = y_tiles // 2
    south_reach = (y_tiles - 1) // 2

    tiles = []
    for dx in range(-west_reach, east_reach + 1):
        for dy in range(-south_reach, north_reach + 1):
            tiles.append((center_x + dx, center_y + dy))
    return tiles


class TileEffect(EffectScript):
    def at_script_creation(self):
        super().at_script_creation()
        self.db.tile_color = ""

        self.db.tiles = []

    def apply_to(self, obj):
        pass

    def at_script_delete(self, **kwargs):
        super().at_script_delete()
        try:
            self.obj.db.combat_turnhandler.db.grid.db.effects.remove(self)
        except AttributeError:
            pass
        return True


class DurationTileEffect(TileEffect, DurationEffect):
    pass


class TileDamage(DurationTileEffect):

    def at_script_creation(self):
        super().at_script_creation()
        self.db.damage_type = None
        self.db.range = ()

    def apply_to(self, obj):
        if not obj.attributes.has("hp"):
            return
        rng = self.db.range
        dmg = randint(rng[0], rng[1])
        obj.location.msg_contents(f"{obj.get_display_name(capital=True)} takes {appearance.dmg_color(obj)}{dmg} "
                                  f"damage|n from {self.db.source.key}!")
        obj.apply_damage({self.db.damage_type: dmg})

