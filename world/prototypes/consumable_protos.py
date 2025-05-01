from decimal import Decimal as Dec

from combat.combat_constants import SECS_PER_TURN

POTION = {
    "typeclass": "typeclasses.inanimate.items.usables.Potion"
}

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
                "amount": 1
            }
        ]
    },
    "weight": round(Dec(0.5), 1),
}
ANTIDOTE = {
    "prototype_parent": "POTION",
    "key": "antidote",
    "desc": "An antidote to poison.",
    "item_func": "cure_condition",
    "kwargs": {
        "effects_cured": ["Poisoned"]
    },
}

HEALTH_POTION = {
    "prototype_parent": "POTION",
    "key": "health potion",
    "desc": "A potion of health",
    "item_func": "heal",
    "kwargs": {
        "range": (20, 30)
    },
}

MANA_POTION = {
    "prototype_parent": "POTION",
    "key": "mana potion",
    "desc": "A potion of mana",
    "item_func": "restore_mana",
    "kwargs": {
        "range": (20, 30)
    },
}

STAMINA_POTION = {
    "prototype_parent": "POTION",
    "key": "stamina potion",
    "desc": "A potion of stamina",
    "item_func": "restore_stamina",
    "kwargs": {
        "range": (20, 30)
    },
}

HP_REGEN_POTION = {
    "prototype_parent": "POTION",
    "key": "regeneration potion",
    "desc": "A portion of life regeneration",
    "item_func": "add_effect",
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
}

VITALITY_POTION = {
    "prototype_parent": "POTION",
    "key": "vitality potion",
    "desc": "A portion increasing maximum hitpoints",
    "item_func": "add_effect",
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
}

