from turnbattle.effects import *

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
                "duration": 15,
                "damage_type": 7
            }
        ]
    },
}
ANTIDOTE = {
    "key": "antidote",
    "typeclass": "typeclasses.inanimate.items.usables.Consumable",
    "desc": "Antidote to cure poisoning.",
    "item_func": "cure_condition",
    "item_uses": 1,
    "kwargs": {
        "effects_cured": ["Poisoned"]
    },
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
                "stat": "hp",
                "range": (1, 1),
                "duration": 15
            }
        ]
    },
}

