from decimal import Decimal as Dec

POISON_DART = {
    "key": "poison dart",
    "typeclass": "typeclasses.inanimate.items.usables.Consumable",
    "desc": "A thin dart coated in deadly poison. Can be used on enemies in combat.",
    "item_func": "add_effect",
    "item_notself": True,
    "item_uses": 1,
    "kwargs": {
        "effects": [
            {
                "script_key": "DamageOverTime",
                "effect_key": "Poisoned",
                "range": (1, 1),
                "duration": 12,
                "damage_type": 7
            }
        ]
    },
    "weight": round(Dec(0.1), 1),
}
ANTIDOTE = {
    "key": "antidote",
    "typeclass": "typeclasses.inanimate.items.usables.Consumable",
    "desc": "An antidote to poison.",
    "item_func": "cure_condition",
    "item_uses": 1,
    "kwargs": {
        "effects_cured": ["Poisoned"]
    },
    "weight": round(Dec(0.2), 1),
}

HEALTH_POTION = {
    "key": "health potion",
    "typeclass": "typeclasses.inanimate.items.usables.Consumable",
    "desc": "A potion of health",
    "item_func": "heal",
    "item_uses": 1,
    "kwargs": {
        "heal_range": (20, 30)
    },
    "weight": Dec(1)
}

HP_REGEN_POTION = {
    "key": "regeneration potion",
    "typeclass": "typeclasses.inanimate.items.usables.Consumable",
    "desc": "A portion of life regeneration",
    "item_func": "add_effect",
    "item_uses": 1,
    "kwargs": {
        "effects": [
            {
                "script_key": "Regeneration",
                "effect_key": "Regenerating HP",
                "stat": "HP",
                "range": (1, 1),
                "duration": 12
            }
        ]
    },
    "weight": Dec(1),
}

