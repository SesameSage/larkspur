from decimal import Decimal as Dec

from combat.effects import DamageTypes

TRAINING_WEAPON = {
    "desc": "Simplified, flimsy, and poorly balanced, but effective for learning one's way around a weapon type.",
    "accuracy_bonus": 0,
    "required_level": 0
}

TRAINING_BLOWGUN = {
    "key": "training blowgun",
    "prototype_parent": "TRAINING_WEAPON",
    "typeclass": "typeclasses.inanimate.items.equipment.weapons.Blowgun",
    "damage_ranges": {DamageTypes.PIERCING: (1, 3)},
    "weight": Dec(1),
    "ap_to_attack": 1
}

TRAINING_BOW = {
    "key": "training bow",
    "prototype_parent": "TRAINING_WEAPON",
    "typeclass": "typeclasses.inanimate.items.equipment.weapons.Bow",
    "damage_ranges": {DamageTypes.PIERCING: (2, 4)},
    "weight": Dec(3),
    "ap_to_attack": 2
}

TRAINING_WAND = {
    "key": "training wand",
    "prototype_parent": "TRAINING_WEAPON",
    "typeclass": "typeclasses.inanimate.items.equipment.weapons.Wand",
    "damage_ranges": {DamageTypes.ARCANE: (2, 4)},
    "weight": Dec(2),
    "ap_to_attack": 2
}

TRAINING_STAFF = {
    "key": "training staff",
    "prototype_parent": "TRAINING_WEAPON",
    "typeclass": "typeclasses.inanimate.items.equipment.weapons.Staff",
    "damage_ranges": {DamageTypes.ARCANE: (3, 5)},
    "weight": Dec(5),
    "ap_to_attack": 2
}

TRAINING_DAGGER = {
    "key": "training dagger",
    "prototype_parent": "TRAINING_WEAPON",
    "typeclass": "typeclasses.inanimate.items.equipment.weapons.Dagger",
    "damage_ranges": {DamageTypes.SLASHING: (1, 3), DamageTypes.PIERCING: (1, 2)},
    "weight": Dec(5),
    "ap_to_attack": 1
}

TRAINING_QUARTERSTAFF = {
    "key": "training quarterstaff",
    "prototype_parent": "TRAINING_WEAPON",
    "typeclass": "typeclasses.inanimate.items.equipment.weapons.Quarterstaff",
    "damage_ranges": {DamageTypes.BLUNT: (3, 5)},
    "weight": Dec(3),
    "ap_to_attack": 2
}

TRAINING_SWORD = {
    "key": "training sword",
    "prototype_parent": "TRAINING_WEAPON",
    "typeclass": "typeclasses.inanimate.items.equipment.weapons.Sword",
    "damage_ranges": {DamageTypes.SLASHING: (2, 3), DamageTypes.PIERCING: (2, 3)},
    "weight": Dec(5),
    "ap_to_attack": 2
}

TRAINING_AXE = {
    "key": "training axe",
    "prototype_parent": "TRAINING_WEAPON",
    "typeclass": "typeclasses.inanimate.items.equipment.weapons.Axe",
    "damage_ranges": {DamageTypes.SLASHING: (4, 6)},
    "weight": Dec(6),
    "ap_to_attack": 2
}

TRAINING_MACE = {
    "key": "training mace",
    "prototype_parent": "TRAINING_WEAPON",
    "typeclass": "typeclasses.inanimate.items.equipment.weapons.Mace",
    "damage_ranges": {DamageTypes.CRUSHING: (4, 6)},
    "weight": Dec(6),
    "ap_to_attack": 2
}

TRAINING_JAVELIN = {
    "key": "training javelin",
    "prototype_parent": "TRAINING_WEAPON",
    "typeclass": "typeclasses.inanimate.items.equipment.weapons.Javelin",
    "damage_ranges": {DamageTypes.PIERCING: (5, 7)},
    "weight": Dec(3),
    "ap_to_attack": 3
}

TRAINING_GREATSWORD = {
    "key": "training greatsword",
    "prototype_parent": "TRAINING_WEAPON",
    "typeclass": "typeclasses.inanimate.items.equipment.weapons.Greatsword",
    "damage_ranges": {DamageTypes.SLASHING: (3, 4), DamageTypes.PIERCING: (3, 4)},
    "weight": Dec(8),
    "ap_to_attack": 3
}

TRAINING_GREATAXE = {
    "key": "training greatsword",
    "prototype_parent": "TRAINING_WEAPON",
    "typeclass": "typeclasses.inanimate.items.equipment.weapons.Greatsword",
    "damage_ranges": {DamageTypes.SLASHING: (6, 9)},
    "weight": Dec(9),
    "ap_to_attack": 3
}

TRAINING_WARHAMMER = {
    "key": "training warhammer",
    "prototype_parent": "TRAINING_WEAPON",
    "typeclass": "typeclasses.inanimate.items.equipment.weapons.Warhammer",
    "damage_ranges": {DamageTypes.BLUNT: (7, 9)},
    "weight": Dec(10),
    "ap_to_attack": 3
}
