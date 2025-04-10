from combat.abilities.abilities import SpellCompAbility
from combat.effects import SECS_PER_TURN


class PoisonArrow(SpellCompAbility):
    def at_object_creation(self):
        super().at_object_creation()
        self.db.targeted = True
        self.db.must_target_entity = True
        self.db.cooldown = 3 * SECS_PER_TURN

        self.db.requirements = {"poison": 3}
