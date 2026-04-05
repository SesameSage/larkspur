from decimal import Decimal as Dec

from combat.combat_constants import DamageTypes


HIDE_BRACERS = {
    "key": "hide bracers",
    "typeclass": "typeclasses.inanimate.items.equipment.apparel.Armwear",
    "weight": Dec(2),

    "defense": {None: 3, DamageTypes.SLASHING: 2, DamageTypes.PIERCING: 1},
    "evasion": 8
}