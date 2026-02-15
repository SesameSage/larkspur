POISON_ARROW = {
    "key": "a poison dart",
    "desc": "An arrow coated in deadly poison. Can be used on enemies in combat when a bow is equipped.",
    "item_func": "attack",
    "item_uses": 1,
    "item_consumable": True,
    "item_kwargs": {
        "damage_range": (5, 10),
        "accuracy": 25,
        "inflict_condition": [("Poisoned", 10)],
    },
}