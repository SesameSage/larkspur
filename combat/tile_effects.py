from combat.effects import EffectScript, DurationEffect


class TileEffect(EffectScript):
    def at_script_creation(self):
        super().at_script_creation()
        self.db.tiles = []
        self.db.tile_color = ""

    def apply_to(self, obj):
        pass


class DurationTileEffect(TileEffect, DurationEffect):
    pass
