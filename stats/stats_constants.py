from decimal import Decimal as Dec

# TODO: Regen values
ATTRIBUTES = {
    "strength": {
        "long_desc": "",
        "affects": "Affects: melee damage, carry weight, max stamina, and use of heavy equipment"
    },
    "constitution": {
        "long_desc": "",
        "affects": "Affects: physical defense, hitpoints, and stamina regeneration"
    },
    "dexterity": {
        "long_desc": "",
        "affects": "Affects: evasion, maximum items carried, use of small and ranged weapons, and turn order"
    },
    "perception": {
        "long_desc": "",
        "affects": "Affects: attack accuracy and detection of sneaking enemies, traps, deception, hidden items, etc."
    },
    "intelligence": {
        "long_desc": "",
        "affects": "Affects: capability to use abilities, lockpicking, alchemy, trapmaking, deception, and deception "
                   "detection"
    },
    "wisdom": {
        "long_desc": "",
        "affects": "Affects: capability to use spells, magic resistance, mana regeneration, amount healed"
    },
    "spirit": {
        "long_desc": "",
        "affects": "Affects: spell power, maximum mana, hitpoint regeneration, and enchanting"
    }}

# <editor-fold desc="Leveling">
XP_THRESHOLD_INCREASES = [  # How much more XP it will take to get to this level than it took to get to the last level
    (2, 100),
    (3, 150),
    (4, 225),
    (5, 350),
    (6, 500),
]
POINTS_GAINED_BY_LEVEL = {  # How many points for increasing different types of stats are gained on attaining each level
    1: {"attribute": 0},
    2: {"attribute": 1},
    3: {"attribute": 0},
    4: {"attribute": 1},
    5: {"attribute": 0},
    6: {"attribute": 1},
}
# </editor-fold>

MAX_HP_BASE = 25  # Base classless amount of HP at Level 1

MAX_MANA_BASE = 20  # Base classless amount of mana at level 1

MAX_STAM_BASE = 20  # Base classless amount of stamina at level 1

# <editor-fold desc="Defense/Resistance/Evasion">
CON_TO_DEFENSE = {  # How much defense is provided by the character's Constitution
    1: 0,
    2: 2,
}
DEXT_TO_EVADE = {  # How much evasion is provided by the character's Dexterity
    1: 0,
    2: 4,
    3: 8,
    4: 12,
    5: 16,
}
WIS_TO_RESIST = {  # How much magic resistance is provided by the character's Wisdom
    1: 0,
}
# </editor-fold>

# <editor-fold desc="Carry/Equip">
BASE_CARRY_WEIGHT = Dec(30)  # The minimum weight all players can carry
STR_TO_CARRY_WEIGHT = {  # How much carry weight is added by the character's Strength
    1: Dec(0),
    2: Dec(5),
    3: Dec(10),
    4: Dec(20),
    5: Dec(35),
    6: Dec(55),
    7: Dec(80),
}
BASE_CARRY_COUNT = 10  # Minimum number of items all players can carry
DEX_TO_CARRY_COUNT = {  # How many more items can be carried based on the character's Dexterity
    1: 0,
    2: 1,
    3: 2,
    4: 4,
    5: 6,
    6: 8,
    7: 10,
}
# </editor-fold>
