from decimal import Decimal as Dec

from combat.effects import DamageTypes

TRAINING_WEAPON = {
    "desc": "Simplified, flimsy, and poorly balanced, but effective for learning one's way around a weapon type.",
    "accuracy_bonus": 10,
    "required_level": 0
}

TRAINING_QUARTERSTAFF = {
    "key": "training quarterstaff",
    "prototype_parent": "TRAINING_WEAPON",
    "typeclass": "typeclasses.inanimate.items.equipment.weapons.Quarterstaff",
    "damage_ranges": {DamageTypes.BLUNT: (5, 10)},
    "weight": Dec(4),
}

