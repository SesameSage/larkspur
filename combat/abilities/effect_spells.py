from combat.abilities.spells import Spell
from combat.effects import DurationEffect, SECS_PER_TURN, Frozen, Drain
from typeclasses.base.objects import Object
from typeclasses.living.living_entities import LivingEntity


class BlindingBeam(Spell):
    """Causes Blindness, halving target's hitrolls."""
    key = "Blinding Beam"

    def at_object_creation(self):
        super().at_object_creation()
        self.key = "Blinding Beam"
        self.db.desc = "Blind your target with a focused beam of bright light."
        self.db.targeted = True
        self.db.must_target_entity = True
        self.db.cost = ("mana", 5)
        self.db.cooldown = 6 * SECS_PER_TURN

    def func(self, caster: LivingEntity, target: Object = None):
        caster.location.msg_contents(f"{caster.get_display_name()} aims a focused beam of blinding white light into "
                                     f"{target.get_display_name()}'s eyes!")
        target.add_effect(DurationEffect, [("effect_key", "Blinded"), ("duration", 3 * SECS_PER_TURN)])
        return True


class Freeze(Spell):
    def at_object_creation(self):
        super().at_object_creation()
        self.db.desc = "Encase your opponent in ice, preventing them from acting at all on their turn."
        self.db.targeted = True
        self.db.must_target_entity = False
        self.db.cost = ("mana", 12)
        self.db.cooldown = 6 * SECS_PER_TURN

    def func(self, caster: LivingEntity, target: Object = None):
        if target.effect_active("Burning"):
            target.scripts.get("Burning").delete()

        target.location.msg_contents(f"{caster.get_display_name(capital=True)} raises nearby water with downturned "
                                     f"fingers, pulls it together to engulf {target.get_display_name(article=True)}, "
                                     f"and separates their hands again in a rapid slicing motion.")

        target.add_effect(Frozen, [("duration", 2 * SECS_PER_TURN)])
        return True


class Curse(Spell):
    def at_object_creation(self):
        super().at_object_creation()
        self.db.desc = "Inflict your opponent with a curse that strikes them whenever they deal damage."
        self.db.targeted = True
        self.db.must_target_entity = True
        self.db.cost = ("mana", 8)
        self.db.cooldown = 4 * SECS_PER_TURN

    def func(self, caster: LivingEntity, target: Object = None):
        caster.location.msg_contents(f"{caster.get_display_name(capital=True)} recites a horrid curse in "
                                     f"{target.get_display_name()}'s name!")
        spirit = caster.get_attr("spirit")
        if target.get_resistance() > 1.75 * spirit:
            caster.location.msg_contents(f"{target.get_display_name(capital=True)} wards off the curse!")
            return True
        else:
            attributes = [("effect_key", "Cursed"), ("duration", 2 * SECS_PER_TURN), ("amount", spirit),
                          ("positive", False)]
            target.add_effect(typeclass=DurationEffect, attributes=attributes)
        return True


class Wither(Spell):
    def at_object_creation(self):
        super().at_object_creation()
        self.db.desc = "Cause an opponent's stamina to wither away over time."
        self.db.targeted = True
        self.db.must_target_entity = True
        self.db.cost = ("mana", 8)
        self.db.cooldown = 3 * SECS_PER_TURN

    def func(self, caster: LivingEntity, target: Object = None):
        if target.get_attr("constitution") > caster.get_attr("spirit") * 1.75:
            caster.location.msg_contents(f"{target.get_display_name(capital=True)} holds too much vitality to wither away!")
            return True
        else:
            target.location.msg_contents(f"{caster.get_display_name(capital=True)} casts a trembling over "
                                         f"{target.get_display_name()}'s body, causing their stamina to wither away!")
            attributes = [("effect_key", "Stamina Drain"), ("stat", "stamina"), ("duration", 5 * SECS_PER_TURN), ("amount", caster.get_attr("spirit"))]
            target.add_effect(typeclass=Drain, attributes=attributes)
            return True