from decimal import Decimal as Dec

from combat.effects import SECS_PER_TURN

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
                "script_key": "Poisoned",
                "range": (1, 1),
                "duration": 3 * SECS_PER_TURN,
            }
        ]
    },
    "weight": round(Dec(0.5), 1),
}
ANTIDOTE = {
    "key": "antidote",
    "typeclass": "typeclasses.inanimate.items.usables.Potion",
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
    "typeclass": "typeclasses.inanimate.items.usables.Potion",
    "desc": "A potion of health",
    "item_func": "heal",
    "item_uses": 1,
    "kwargs": {
        "range": (20, 30)
    },
    "weight": round(Dec(1), 1),
}

MANA_POTION = {
    "key": "mana potion",
    "typeclass": "typeclasses.inanimate.items.usables.Potion",
    "desc": "A potion of mana",
    "item_func": "restore_mana",
    "item_uses": 1,
    "kwargs": {
        "range": (20, 30)
    },
    "weight": round(Dec(1), 1),
}

STAMINA_POTION = {
    "key": "stamina potion",
    "typeclass": "typeclasses.inanimate.items.usables.Potion",
    "desc": "A potion of stamina",
    "item_func": "restore_stamina",
    "item_uses": 1,
    "kwargs": {
        "range": (20, 30)
    },
    "weight": round(Dec(1), 1),
}

HP_REGEN_POTION = {
    "key": "regeneration potion",
    "typeclass": "typeclasses.inanimate.items.usables.Potion",
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
                "duration": 5 * SECS_PER_TURN
            }
        ]
    },
    "weight": round(Dec(1), 1),
}

VITALITY_POTION = {
    "key": "vitality potion",
    "typeclass": "typeclasses.inanimate.items.usables.Potion",
    "desc": "A portion increasing maximum hitpoints",
    "item_func": "add_effect",
    "item_uses": 1,
    "kwargs": {
        "effects": [
            {
                "script_key": "TimedStatMod",
                "effect_key": "Max HP",
                "stat": "HP",
                "amount": 10,
                "duration": 20 * SECS_PER_TURN
            }
        ]
    },
    "weight": round(Dec(1), 1),
}

