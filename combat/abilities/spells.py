from combat.abilities.abilities import *


class Spell(Ability):
    """Spells differ from Abilities only in name and appearance. Spells are generally cast by Sorcerers, Clerics,
    Witches, and Druids."""

    def color(self):
        return appearance.spell


class SustainedSpell(SustainedAbility, Spell):
    pass


class TileSpell(TileAbility, Spell):
    def color(self):
        return Spell.color(self)
