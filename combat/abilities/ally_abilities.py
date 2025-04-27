from combat.abilities.abilities import Ability
from combat.effects import SECS_PER_TURN, TimedStatMod
from typeclasses.base.objects import Object
from typeclasses.living.living_entities import LivingEntity


class MindClearingTone(Ability):
    key = "Mind-Clearing Tone"

    def at_object_creation(self):
        super().at_object_creation()
        self.db.desc = "This meditational tone improves the accuracy of you and your allies."
        self.db.targeted = False
        self.db.requires = [("wisdom", 5)]
        self.db.cost = [("mana", 12)]
        self.db.cooldown = 5 * SECS_PER_TURN

    def func(self, caster: LivingEntity, target: Object = None):
        # TODO: Count what are allies outside of combat
        # TODO: Sustained spells and abilities
        attributes = [("effect_key", "+Accuracy"), ("amount", 15), ("duration", 3 * SECS_PER_TURN)]
        if not caster.is_in_combat():
            caster.msg("This ability can't be used out of combat yet.")
            return
        else:
            caster.location.msg_contents(f"{caster.get_display_name(capital=True)} begins a mind-clearing monotonous "
                                         f"hum.")
            for fighter in caster.db.combat_turnhandler.db.fighters:
                if fighter.db.hostile_to_players == caster.db.hostile_to_players:
                    fighter.add_effect(typeclass=TimedStatMod, attributes=attributes)
