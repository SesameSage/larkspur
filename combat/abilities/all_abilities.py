import importlib
import inspect

from combat.abilities.abilities import Ability

ALL_ABILITIES = {}

for filename in [".ally_spells", ".damage_abilities", ".damage_spells", ".effect_abilities", ".effect_spells",
                 ".protective_abilities", ".protective_spells", ".self_spells"]:
    members = inspect.getmembers(importlib.import_module(filename, package="combat.abilities"))
    for member in members:
        if not isinstance(member[1], type):
            continue
        if issubclass(member[1], Ability):
            if member[0] in [
                "Ability", "Spell", "SpellCompAbility", "SustainedAbility", "SpellCompSpell", "SustainedSpell"
            ]:
                continue
            else:
                key = (member[1].key if isinstance(member[1].key, str) else member[0])
                ALL_ABILITIES[key] = member[1]


def get(inpt):
    for ability_name in ALL_ABILITIES:
        if ability_name.lower().startswith(inpt.lower()):
            return ALL_ABILITIES[ability_name]
