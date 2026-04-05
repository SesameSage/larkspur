from decimal import Decimal as Dec

from combat.combat_constants import DamageTypes


KINETIC_FOOTWRAPS = {
    "key": "kinetic footwraps",
    "typeclass": "typeclasses.inanimate.items.equipment.apparel.Footwear",
    "weight": Dec(0.5),

    "defense": {None: 1},
    "evasion": 10,
    "equip_effects": {
        "Max Stamina": 10,
        "+Dexterity": 2
    }
}