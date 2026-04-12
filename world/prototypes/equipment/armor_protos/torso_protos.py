from decimal import Decimal as Dec

from combat.combat_constants import DamageTypes

LEATHER_VEST = {
    "key": "leather vest",
    "typeclass": "typeclasses.inanimate.items.item_types.equipment.torso.Vest",
    "weight": Dec(7),

    "defense": {None: 5, DamageTypes.SLASHING: 4, DamageTypes.PIERCING: 2},
    "evasion": 15
}