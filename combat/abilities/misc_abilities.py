from combat.abilities.abilities import Ability
from combat.combat_constants import SECS_PER_TURN
from typeclasses.scripts.weather import RAINING


class RainDance(Ability):
    key = "Rain Dance"
    desc = "Beckon rain from the heavens."

    def at_object_creation(self):
        super().at_object_creation()
        self.db.targeted = False

        self.db.requires = [("intelligence", 1)]
        self.db.ap_cost = 1
        self.db.cost = [("mana", 5)]
        self.db.cooldown = 30 * SECS_PER_TURN

    def check(self, caster, target):
        if not super().check(caster, target):
            return False
        if caster.location.zone().db.current_weather == RAINING:
            caster.msg("It is already raining!")
            return False
        return True

    def func(self, caster, target=None):
        caster.location.msg_contents(f"{caster.get_display_name(capital=True)} performs a rain dance!")
        caster.location.zone().update_weather(RAINING)