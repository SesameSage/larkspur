from combat.abilities.abilities import Ability
from combat.combat_handler import COMBAT
from combat.effects import SECS_PER_TURN, TimedStatMod
from typeclasses.base.objects import Object
from typeclasses.living.living_entities import LivingEntity


class MindClearingTone(Ability):
    key = "Mind-Clearing Tone"
    desc = "This meditational tone improves the accuracy of you and your allies."

    def at_object_creation(self):
        super().at_object_creation()
        self.db.targeted = False
        self.db.offensive = False

        self.db.requires = [("wisdom", 5)]
        self.db.cost = [("mana", 12)]
        self.db.cooldown = 5 * SECS_PER_TURN

    def func(self, caster: LivingEntity, target: Object = None):
        # TODO: Sustained spells and abilities
        caster.location.msg_contents(f"{caster.get_display_name(capital=True)} begins a mind-clearing monotonous "
                                     f"hum.")

        attributes = [("effect_key", "+Accuracy"), ("amount", 15), ("duration", 3 * SECS_PER_TURN), ("source", self.key)]
        for ally in COMBAT.get_allies(caster):
                ally.add_effect(typeclass=TimedStatMod, attributes=attributes)
