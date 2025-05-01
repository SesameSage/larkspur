from decimal import Decimal as Dec

# TODO: Regen values

# <editor-fold desc="Leveling">
XP_THRESHOLD_INCREASES = [  # How much more XP it will take to get to this level than it took to get to the last level
    (2, 100),
    (3, 150),
    (4, 225),
    (5, 350),
    (6, 500),
]
POINTS_GAINED_BY_LEVEL = {  # How many points for increasing different types of stats are gained on attaining each level
    2: {"attribute": 1},
    3: {},
    4: {"attribute": 1},
    5: {},
    6: {"attribute": 1},
}
# </editor-fold>

# <editor-fold desc="Hitpoints">
MAX_HP_BASE = 100  # Base classless amount of HP at Level 1
LVL_TO_MAXHP = {  # How much Max HP is increased for all characters on leveling up
    1: 0,
    2: 10,
}
CON_TO_MAXHP = {  # How much Max HP is added by character's Constitution
    1: 0,
    2: 10,
}
# </editor-fold>

# <editor-fold desc="Mana">
MAX_MANA_BASE = 50  # Base classless amount of mana at level 1
LVL_TO_MAXMANA = {  # How much Max Mana is increased for all classes on leveling up
    1: 0,
}
SPIRIT_TO_MAXMANA = {  # How much Max Mana is added by character's Spirit
    1: 0,
    2: 10,
}
# </editor-fold>

# <editor-fold desc="Stamina">
MAX_STAM_BASE = 50  # Base classless amount of stamina at level 1
LVL_TO_MAXSTAM = {  # How much all classes' Max Stamina increases per level
    1: 0,
    2: 5,
}
STR_TO_MAXSTAM = {  # How much Max Stamina is added by character's Strength
    1: 0,
    2: 10,
    3: 15,
    4: 25,
    5: 35
}
# </editor-fold>

# <editor-fold desc="Defense/Resistance/Evasion">
CON_TO_DEFENSE = {  # How much defense is provided by the character's Constitution
    1: 0,
    2: 2,
}
DEXT_TO_EVADE = {  # How much evasion is provided by the character's Dexterity
    1: 0,
    2: 5,
    3: 10,
    4: 20,
    5: 30
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
    2: 2,
    3: 3,
    4: 5,
    5: 7,
    6: 10,
}
# </editor-fold>
