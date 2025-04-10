from combat.abilities.abilities import *


class Spell(Ability):
    def color(self):
        return appearance.spell


class SustainedSpell(SustainedAbility, Spell):
    pass


