from combat.combat_constants import SECS_PER_TURN


ARROW = {
    "typeclass": "typeclasses.inanimate.items.usables.Arrow",
    "item_func": "attack",
}
POISON_ARROW = {
    "prototype_parent": "ARROW",
    "key": "poison arrow",
    "desc": "An arrow coated in deadly poison. Can be used on enemies in combat when a bow is equipped.",
    "item_kwargs": {
        "effects_inflicted": [{
                "script_key": "Poisoned",
                "range": (1, 3),
                "duration": 3 * SECS_PER_TURN
            }],
    },
}