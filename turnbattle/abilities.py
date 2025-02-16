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
        self.db.cooldown = 0

    def cast(self, caster: LivingEntity, target: Object = None):
        super().cast(caster, target)
        duration = 10
        # TODO: ints to decimals in effect scripts
        duration += caster.get_attr(CharAttrib.STRENGTH) * 0.25
        duration -= target.get_attr(CharAttrib.DEXTERITY) * 0.25
        target.scripts.add(Knockdown(duration))


