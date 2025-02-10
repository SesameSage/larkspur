from turnbattle.rules import COMBAT_RULES

ITEMFUNCS = {
    "heal": COMBAT_RULES.itemfunc_heal,
    "attack": COMBAT_RULES.itemfunc_attack,
    "add_condition": COMBAT_RULES.itemfunc_add_condition,
    "cure_condition": COMBAT_RULES.itemfunc_cure_condition,
}
