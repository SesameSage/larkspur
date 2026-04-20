from enum import Enum
from decimal import Decimal as Dec

class DamageTypes(Enum):
    BLUNT = 1
    SLASHING = 2
    PIERCING = 3
    ARCANE = 5
    FIRE = 6
    COLD = 7
    SHOCK = 8

    def get_display_name(self, capital=False):
        name = self.name.lower()
        if capital:
            name = name.capitalize()
        return name

DIRECTION_NAMES_OPPOSITES = { # Quick reference for which direction names are opposites
        "n": ("north", "s"),
        "ne": ("northeast", "sw"),
        "e": ("east", "w"),
        "se": ("southeast", "nw"),
        "s": ("south", "n"),
        "sw": ("southwest", "ne"),
        "w": ("west", "e"),
        "nw": ("northwest", "se"),
        "u": ("up", "d"),
        "d": ("down", "u"),
        "i": ("in", "o"),
        "o": ("out", "i"),
    }

TURN_TIMEOUT = 30  # Time before turns automatically end, in seconds
SECS_PER_TURN = 3  # How many real-time seconds each combat turn simulates
RAIN_FIRE_DMG_REDUCTION = Dec(0.7)  # What percentage fire damage should be reduced to in the rain


