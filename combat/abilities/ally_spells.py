"""Beneficial spells cast on an ally."""

from combat.abilities.spells import Spell
from combat.combat_constants import SECS_PER_TURN
from typeclasses.base.objects import Object
from typeclasses.living.living_entities import LivingEntity


class Cleanse(Spell):
    desc = "Remove a temporary negative effect from an ally."

    def at_object_creation(self):
        super().at_object_creation()
        self.db.targeted = True
        self.db.must_target_entity = True
        self.db.offensive = False

        self.db.requires = [("spirit", 3)]
        self.db.ap_cost = 4
        self.db.cost = [("mana", 12)]
        self.db.cooldown = 5 * SECS_PER_TURN

    def func(self, caster: LivingEntity, target: Object = None):
        target.location.msg_contents(f"{caster.get_display_name(capital=True)} shines a cleansing light on "
                                     f"{target.get_display_name()}.")
        for script in target.scripts.all():
            if script.db.duration and not script.db.positive:
                script.add_seconds(amt=script.db.duration)
                script.check_duration()
                return True
        target.location.msg(f"Couldn't find a negative effect on {target.get_display_name()}!")
        return False


class HealWounds(Spell):
    key = "Heal Wounds"
    desc = "Restore some of an ally's HP."

    def at_object_creation(self):
        super().at_object_creation()
        self.db.targeted = True
        self.db.must_target_entity = True
        self.db.offensive = False

        self.db.requires = [("spirit", 2)]
        self.db.ap_cost = 3
        self.db.cost = [("mana", 12)]
        self.db.cooldown = 3 * SECS_PER_TURN

    def func(self, caster: LivingEntity, target: Object = None):
        target.location.msg_contents(f"{caster.get_display_name(capital=True)} immerses "
                                     f"{target.get_display_name(article=True)}'s wounds in holy water.")
        amt_healed = caster.get_attr("spirit") * 10
        amt_can_be_healed = target.get_max("hp") - target.db.hp
        if amt_healed > amt_can_be_healed:
            amt_healed = amt_can_be_healed
        target.db.hp += amt_healed
        target.location.msg_contents(f"{target.get_display_name(capital=True)} restores {amt_healed} HP!")


class Revive(Spell):
    desc = "Bring back an ally who has been knocked out."

    def at_object_creation(self):
        super().at_object_creation()
        self.db.targeted = True
        self.db.must_target_entity = True
        self.db.offensive = False

        self.db.requires = [("spirit", 10)]
        self.db.cost = [("mana", 25)]
        self.db.cooldown = 10 * SECS_PER_TURN

    def check(self, caster, target):
        if not super().check(caster, target):
            return False

        if target.db.hp > 0:
            caster.msg(target.name + " isn't knocked out!")
            return False

        return True

    def func(self, caster: LivingEntity, target: Object = None):
        target.db.hp = 50
        target.location.msg_contents(target.get_display_name() + " has been revived!")
