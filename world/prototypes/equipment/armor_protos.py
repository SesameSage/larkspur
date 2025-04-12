from decimal import Decimal as Dec

from combat.effects import DamageTypes

LEATHER_VEST = {
    "key": "leather vest",
    "typeclass": "typeclasses.inanimate.items.equipment.apparel.Torsowear",
    "weight": Dec(7),

    "defense": {None: 5, DamageTypes.SLASHING: 4, DamageTypes.PIERCING: 2},
    "evasion": 15
}
KINETIC_FOOTWRAPS = {
    "key": "kinetic footwraps",
    "typeclass": "typeclasses.inanimate.items.equipment.apparel.Footwraps",
    "weight": Dec(0.5),

    "defense": {None: 1},
    "evasion": 15,
}
HIDE_BRACERS = {
    "key": "hide bracers",
    "typeclass": "typeclasses.inanimate.items.equipment.apparel.Armwear",
    "weight": Dec(2),

    "defense": {None: 3, DamageTypes.SLASHING: 2, DamageTypes.PIERCING: 1},
    "evasion": 8
}