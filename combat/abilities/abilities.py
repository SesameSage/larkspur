from combat.effects import *
from typeclasses.base.objects import Object
from typeclasses.inanimate.items.spellcomp import SpellComp
from typeclasses.living.living_entities import LivingEntity


# TODO: Show abilities

class Ability(Object):

    def at_object_creation(self):
        if not self.key:
            self.key = self.__class__.__name__
        self.locks.add("view:false()")
        self.db.desc = ""
        self.db.action_text = ""
        self.db.targeted = False
        self.db.must_target_entity = False
        self.db.cost = None
        self.db.cooldown = 0

    def cast(self, caster: LivingEntity, target: Object = None):
        if not self.check(caster, target):
            return False
        else:
            self.adjust_cooldowns_stats(caster)
            self.func(caster, target)
            return True

    def check(self, caster, target):
        """
        Checks whether an ability/spell can be cast and is being cast properly before running any casting logic.
        Args:
            caster: Entity calling the ability/spell.
            target: Entity targeted, if any.

        Returns:
            Boolean whether the check passed.
        """
        if self.db.cost:  # If ability costs mana/stamina
            if caster.attributes.get(self.db.cost[0]) < self.db.cost[1]:  # If caster doesn't have enough
                caster.msg("Not enough " + self.db.cost[0] + "!")
                return False
        if self.db.cooldown > 0 and not caster.is_superuser:  # If ability has a cooldown
            try:
                if caster.db.cooldowns[self.key] > 0:  # If caster has cooldown time remaining
                    if caster.is_in_combat():  # Convert seconds to turns
                        amount_string = f"{int(caster.db.cooldowns[self.key] // SECS_PER_TURN)} turns"
                    else:
                        amount_string = f"{caster.db.cooldowns[self.key]} seconds"
                    caster.msg(
                        f"{appearance.notify}{amount_string} cooldown remaining to cast {self.key}")
                    return False
            except KeyError:
                caster.db.cooldowns[self.key] = 0
        if self.db.targeted:  # If ability is meant to target something
            if target and target is not None:
                # This may cause a circular import eventually to not work around
                if self.db.must_target_entity:
                    if not inherits_from(target, LivingEntity):
                        caster.msg(f"{self.name} must target a living thing")
                        return False
                if target.attributes.has("hp"):
                    if target.db.hp < 1 and self.__class__.__name__ != "Revive":
                        caster.msg(f"{target.name} has been defeated!")
                        return False
            else:
                caster.msg(f"{self.name} must have a target")
                return False
        return True

    def func(self, caster: LivingEntity, target: Object = None):
        """
        Performs the ability's function.
        Args:
            caster: Entity calling the ability/spell.
            target: Entity targeted, if any
        """
        pass

    def adjust_cooldowns_stats(self, caster):
        """
        Reset ability cooldown on caster, and remove cost from their mana/stamina.
        """
        if self.db.cooldown > 0:
            caster.db.cooldowns[self.key] = self.db.cooldown
        if self.db.cost:
            match self.db.cost[0]:
                case "mana":
                    caster.db.mana -= self.db.cost[1]
                case "stamina":
                    caster.db.stamina -= self.db.cost[1]

    def color(self):
        return appearance.ability


class SustainedAbility(Ability):
    def at_object_creation(self):
        super().at_object_creation()
        self.db.duration = None


class SpellCompAbility(Ability):

    def at_object_creation(self):
        self.db.requirements = {}

    def check(self, caster, target):
        if super().check(caster, target):
            for requirement in self.db.requirements:
                available = [item for item in caster.contents if
                             isinstance(item, SpellComp) and requirement in item.db.uses]
                if len(available) < 1:
                    caster.msg(f"No spellcomp with {requirement}!")
                    return False
                lowest_val_item_usable = available[0]
                items_to_use = []
                for candidate in available:
                    if candidate.get_strength(requirement) >= self.db.requirements[requirement]:
                        items_to_use.append(candidate)
                        if candidate.get_strength(requirement) <= lowest_val_item_usable.get_strength(requirement):
                            lowest_val_item_usable = candidate
            if len(items_to_use) < 1:
                caster.msg(f"No spellcomp with sufficient {requirement}!")
                return False
            return [lowest_val_item_usable]
        else:
            return False

    def func(self, caster: LivingEntity, target: Object = None):
        items_to_use = self.check(caster, target)
        for item in items_to_use:
            item.delete()
        caster.msg(f"Used: {[item.name for item in items_to_use]}")
        self.adjust_cooldowns_stats(caster)
        return True
