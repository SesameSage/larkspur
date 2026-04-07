from decimal import Decimal as Dec

from combat.combat_constants import DamageTypes

path = "typeclasses.inanimate.items.equipment.head."

LEATHER_CAP = {
    "key": "leather cap",
    "typeclass": "Helmet",
    "weight": Dec(3),

    "defense": {None: 2, DamageTypes.SLASHING: 1, DamageTypes.PIERCING: 1},
    "evasion": 2
}
CLOTH_HOOD = {
    "key": "cloth hood",
    "typeclass": "typeclasses.inanimate.items.equipment.head.Hood",
    "weight": Dec(2),

    "evasion": 5,
}