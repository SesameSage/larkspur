from enum import Enum

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

DIRECTION_NAMES_OPPOSITES = {
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

SECS_PER_TURN = 3  # How many real-time seconds each combat turn simulates
PERCEPT_TO_ACCURACY_BONUS = {  # How much is added to character's hit rolls by their Perception
    1: 5,
    2: 10,
    3: 15,
    4: 20,
    5: 25
}


