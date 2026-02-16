from combat.combat_constants import SECS_PER_TURN

POISON_ARROW = {
    "key": "a poison dart",
    "typeclass": "typeclasses.inanimate.items.usables.Arrow",
    "desc": "An arrow coated in deadly poison. Can be used on enemies in combat when a bow is equipped.",
    "item_func": "attack",
    "item_uses": 1,
    "item_consumable": True,
    "item_kwargs": {
        "damage_range": (5, 10),
        "accuracy": 25,
        "effects_inflicted": [{
                "script_key": "Poisoned",
                "range": (1, 3),
                "duration": 3 * SECS_PER_TURN
            }],
    },
}