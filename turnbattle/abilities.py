from evennia.utils import inherits_from

from turnbattle.effects import *
from typeclasses.base.objects import Object
from typeclasses.living.char_stats import CharAttrib
from typeclasses.living.living_entities import LivingEntity


class Ability(Object):

    def at_object_creation(self):
        self.locks.add("view:false()")
        self.db.desc = ""
        self.db.action_text = ""
        self.db.targeted = False
        self.db.must_target_entity = True
        self.db.cost = None
        self.db.cooldown = 0

    def check(self, caster, target):
        if self.db.cost:
            if caster.attributes.get(self.db.cost[0]) < self.db.cost[1]:
                caster.msg("Not enough " + self.db.cost[0] + "!")
                return False
        if self.db.cooldown > 0:
            try:
                if caster.db.cooldowns[self.key] > 0:
                    caster.msg(f"{appearance.notify}{caster.db.cooldowns[self.key]} seconds cooldown remaining to cast {self.key}")
                    return False
            except KeyError:
                caster.db.cooldowns[self.key] = 0
        if self.db.targeted:
            if target and target is not None:
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
            if self.db.cost:
                match self.db.cost[0]:
                    case "mana":
                        caster.db.mana -= self.db.cost[1]
                    case "stamina":
                        caster.db.stamina -= self.db.cost[1]
            return True

    def get_display_name(self, looker=None, capital=False, **kwargs):
        return appearance.ability + self.name


class SustainedAbility(Ability):
    def at_object_creation(self):
        super().at_object_creation()
        self.db.duration = None


class Sweep(Ability):
    def at_object_creation(self):
        super().at_object_creation()
        self.db.targeted = True
        self.db.must_target_entity = True
        self.db.cost = ("stamina", 1)
        self.db.cooldown = 15

    def cast(self, caster: LivingEntity, target: Object = None):
        if not super().cast(caster, target):
            return False
        weapon_weight = caster.get_weapon().db.weight if caster.get_weapon() else 0
        if target.get_attr(CharAttrib.CONSTITUTION) > caster.get_attr(CharAttrib.STRENGTH) + weapon_weight:
            caster.location.msg_contents(f"{target.get_display_name()} stands too strong for {caster.get_display_name()}'s"
                                         f" sweep of the legs!")
        elif target.get_attr(CharAttrib.DEXTERITY) > caster.get_attr(CharAttrib.DEXTERITY):
            caster.location.msg_contents(f"{target.get_display_name()}'s quick footwork avoids {caster.get_display_name()}'s "
                                         f"sweep!")
        else:
            target.location.msg_contents(f"{caster.get_display_name()} sweeps at {target.get_display_name()}'s legs, "
                                         f"knocking them to the ground!")
            target.add_effect(KnockedDown, (("effect_key", "Knocked Down"), ("duration", 6)))
        return True


