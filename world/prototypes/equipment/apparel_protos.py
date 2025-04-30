from decimal import Decimal as Dec

COROLLA = {
    "typeclass": "typeclasses.inanimate.items.equipment.head.Circlet",
    "weight": Dec(3),
}

WILLOW_COROLLA = {
    "prototype_parent": "COROLLA",
    "key": "willow corolla",

    "resistance": {None: 2},
    "evasion": 2,
    "equip_effects": {
        "Max Mana": 15
    }
}
