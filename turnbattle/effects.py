from turnbattle.rules import COMBAT_RULES

ITEMFUNCS = {
    "heal": COMBAT_RULES.itemfunc_heal,
    "attack": COMBAT_RULES.itemfunc_attack,
    "add_condition": COMBAT_RULES.itemfunc_add_condition,
    "cure_condition": COMBAT_RULES.itemfunc_cure_condition,
}
"""
----------------------------------------------------------------------------
PROTOTYPES START HERE
----------------------------------------------------------------------------

You can paste these prototypes into your game's prototypes.py module in your
/world/ folder, and use the spawner to create them - they serve as examples
of items you can make and a handy way to demonstrate the system for
conditions as well.

Items don't have any particular typeclass - any object with a db entry
"item_func" that references one of the functions given above can be used as
an item with the 'use' command.

Only "item_func" is required, but item behavior can be further modified by
specifying any of the following:

    item_uses (int): If defined, item has a limited number of uses

    item_selfonly (bool): If True, user can only use the item on themself

    item_consumable(True or str): If True, item is destroyed when it runs
        out of uses. If a string is given, the item will spawn a new
        object as it's destroyed, with the string specifying what prototype
        to spawn.

    item_kwargs (dict): Keyword arguments to pass to the function defined in
        item_func. Unique to each function, and can be used to make multiple
        items using the same function work differently.
"""
MEDKIT = {
    "key": "a medical kit",
    "aliases": ["medkit"],
    "desc": "A standard medical kit. It can be used a few times to heal wounds.",
    "item_func": "heal",
    "item_uses": 3,
    "item_consumable": True,
    "item_kwargs": {"healing_range": (15, 25)},
}

GLASS_BOTTLE = {"key": "a glass bottle", "desc": "An empty glass bottle."}

HEALTH_POTION = {
    "key": "a health potion",
    "desc": "A glass bottle full of a mystical potion that heals wounds when used.",
    "item_func": "heal",
    "item_uses": 1,
    "item_consumable": "GLASS_BOTTLE",
    "item_kwargs": {"healing_range": (35, 50)},
}

REGEN_POTION = {
    "key": "a regeneration potion",
    "desc": "A glass bottle full of a mystical potion that regenerates wounds over time.",
    "item_func": "add_condition",
    "item_uses": 1,
    "item_consumable": "GLASS_BOTTLE",
    "item_kwargs": {"conditions": [("Regeneration", 10)]},
}

HASTE_POTION = {
    "key": "a haste potion",
    "desc": "A glass bottle full of a mystical potion that hastens its user.",
    "item_func": "add_condition",
    "item_uses": 1,
    "item_consumable": "GLASS_BOTTLE",
    "item_kwargs": {"conditions": [("Haste", 10)]},
}

BOMB = {
    "key": "a rotund bomb",
    "desc": "A large black sphere with a fuse at the end. Can be used on enemies in combat.",
    "item_func": "attack",
    "item_uses": 1,
    "item_consumable": True,
    "item_kwargs": {"damage_range": (25, 40), "accuracy": 25},
}

POISON_DART = {
    "key": "a poison dart",
    "desc": "A thin dart coated in deadly poison. Can be used on enemies in combat",
    "item_func": "attack",
    "item_uses": 1,
    "item_consumable": True,
    "item_kwargs": {
        "damage_range": (5, 10),
        "accuracy": 25,
        "inflict_condition": [("Poisoned", 10)],
    },
}

TASER = {
    "key": "a taser",
    "desc": "A device that can be used to paralyze enemies in combat.",
    "item_func": "attack",
    "item_kwargs": {
        "damage_range": (10, 20),
        "accuracy": 0,
        "inflict_condition": [("Paralyzed", 1)],
    },
}

GHOST_GUN = {
    "key": "a ghost gun",
    "desc": "A gun that fires scary ghosts at people. Anyone hit by a ghost becomes frightened.",
    "item_func": "attack",
    "item_uses": 6,
    "item_kwargs": {
        "damage_range": (5, 10),
        "accuracy": 15,
        "inflict_condition": [("Frightened", 1)],
    },
}

ANTIDOTE_POTION = {
    "key": "an antidote potion",
    "desc": "A glass bottle full of a mystical potion that cures poison when used.",
    "item_func": "cure_condition",
    "item_uses": 1,
    "item_consumable": "GLASS_BOTTLE",
    "item_kwargs": {"to_cure": ["Poisoned"]},
}

AMULET_OF_MIGHT = {
    "key": "The Amulet of Might",
    "desc": "The one who holds this amulet can call upon its power to gain great strength.",
    "item_func": "add_condition",
    "item_selfonly": True,
    "item_kwargs": {"conditions": [("Damage Up", 3), ("Accuracy Up", 3), ("Defense Up", 3)]},
}

AMULET_OF_WEAKNESS = {
    "key": "The Amulet of Weakness",
    "desc": "The one who holds this amulet can call upon its power to gain great weakness. "
            "It's not a terribly useful artifact.",
    "item_func": "add_condition",
    "item_selfonly": True,
    "item_kwargs": {"conditions": [("Damage Down", 3), ("Accuracy Down", 3), ("Defense Down", 3)]},
}
