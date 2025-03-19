from turnbattle.effects import *

POISON_DART = {
    "key": "a poison dart",
    "typeclass": "typeclasses.inanimate.items.usables.Consumable",
    "desc": "A thin dart coated in deadly poison. Can be used on enemies in combat",
    "item_func": "add_effect",
    "item_notself": True,
    "item_uses": 1,
    "kwargs": {
        "effects": [
            {
                "script_key": "DamageOverTime",
                "effect_key": "Poisoned",
                "range": (1, 1),
                "duration": Dec(15),
                "damage_type": 7
            }
        ]

    },
}