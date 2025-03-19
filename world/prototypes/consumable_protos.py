POISON_DART = {
    "key": "a poison dart",
    "typeclass": "typeclasses.inanimate.items.usables.Consumable",
    "desc": "A thin dart coated in deadly poison. Can be used on enemies in combat",
    "item_func": "attack",
    "item_uses": 1,
    "item_kwargs": {
        "damage_range": (5, 10),
        "accuracy": 25,
        "inflict_condition": [("Poisoned", 10)],
    },
}
