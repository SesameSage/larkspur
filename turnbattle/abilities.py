from evennia.utils import inherits_from

from typeclasses.base.objects import Object
from typeclasses.living.char_stats import CharAttrib
from typeclasses.living.living_entities import LivingEntity
from turnbattle.effects import *


class Ability(Object):

    def at_object_creation(self):
        self.db.desc = ""
        self.db.action_text = ""
        self.db.targeted = False
        self.db.must_target_entity = True
        self.db.cost = None
        self.db.cooldown = 0

    def check(self, caster, target):
        if self.db.cooldown > 0:
            try:
                if caster.db.cooldowns[self.key] > 0:
                    return False
            except KeyError:
                caster.db.cooldowns[self.key] = 0
        if self.db.targeted:
            if target:
                if self.db.must_target_entity:
                    if inherits_from(target, LivingEntity):
                        return True
                    else:
                        caster.msg(f"{self.name} must target a living thing")
                        return False
            else:
                caster.msg(f"{self.name} must have a target")
                return False
        return True

    def cast(self, caster: LivingEntity, target: Object = None):
        if not self.check(caster, target):
            return False
        else:
            if self.db.cooldown > 0:
                caster.db.cooldowns[self.key] = self.db.cooldown


class SustainedAbility(Ability):
    def at_object_creation(self):
        super().at_object_creation()
        self.db.duration = None


class Sweep(Ability):
    def at_object_creation(self):
        super().at_object_creation()
        self.db.targeted = True
        self.db.must_target_entity = True
        self.db.cost = {"stamina": 1}
        self.db.cooldown = 5

    def cast(self, caster: LivingEntity, target: Object = None):
        super().cast(caster, target)
        duration = 10
        duration += caster.get_attr(CharAttrib.STRENGTH) * Dec(0.25)
        duration -= target.get_attr(CharAttrib.DEXTERITY) * Dec(0.25)
        target.scripts.add(KnockedDown(duration))
        return True


