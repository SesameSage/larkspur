from combat.abilities.abilities import *


class Spell(Ability):
    def get_display_name(self, looker=None, capital=False, **kwargs):
        return appearance.spell + self.name


class SustainedSpell(SustainedAbility, Spell):
    pass


