import importlib
import inspect

from evennia.utils import inherits_from

from combat.abilities.ally_spells import HealWounds

ALL_ABILITIES = {}
HEALING_ABILITIES = {"Heal Wounds": HealWounds}

for filename in [".ally_abilities", ".ally_spells", ".damage_abilities", ".damage_spells", ".effect_abilities",
                 ".effect_spells", ".protective_abilities", ".protective_spells", ".self_abilities", ".self_spells",
                 ".team_abilities", ".team_spells"]:
    members = inspect.getmembers(importlib.import_module(filename, package="combat.abilities"))
    for member in members:
        if not isinstance(member[1], type):
            continue
        if inherits_from(member[1], "combat.abilities.abilities.Ability"):
            if member[0] in ["Ability", "Spell", "SustainedAbility", "SustainedSpell", "BowAbility"]:
                continue
            else:
                # Add to all abilities
                key = (member[1].key if isinstance(member[1].key, str) else member[0])
                ALL_ABILITIES[key] = member[1]

ALL_ABILITIES = dict(sorted(ALL_ABILITIES.items()))
HEALING_ABILITIES = dict(sorted(HEALING_ABILITIES.items()))


def get(inpt):
    for ability_name in ALL_ABILITIES:
        if ability_name.lower().startswith(inpt.lower()):
            return ALL_ABILITIES[ability_name]
