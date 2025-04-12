from evennia.utils.create import create_object

from combat.abilities.damage_abilities import Scratch

HELLHOUND = {
    "key": "hellhound",
    "typeclass": "typeclasses.living.creatures.EnemyBeast",
    "char_defense": {None: 5},
    "evasion": 15,
    "abilities": [create_object(typeclass=Scratch, key="Scratch")]
}
