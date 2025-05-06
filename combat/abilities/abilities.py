from combat.combat_handler import COMBAT
from combat.effects import *
from typeclasses.base.objects import Object
from typeclasses.inanimate.items.equipment.weapons import Bow
from typeclasses.living.living_entities import LivingEntity


class Ability(Object):
    help_category = "spells"
    desc = ""

    def at_object_creation(self):
        if not self.key:
            self.key = self.__class__.__name__
        self.db.desc = self.desc
        self.locks.add("view:false()")

        self.db.desc = ""
        self.db.action_text = ""  # Will require parsing {caster} {target} from here to use

        self.db.targeted = False
        self.db.must_target_entity = False
        self.db.offensive = True

        self.db.requires = [()]  # Required attributes to learn (dexterity, wisdom, etc)

        self.db.ap_cost = 2
        self.db.cost = []  # Mana and stamina costs
        self.db.cooldown = 0  # How long before it can be cast again

    def check(self, caster, target):
        """
        Checks whether an ability/spell can be cast and is being cast properly before running any casting logic.
        Args:
            caster: Entity calling the ability/spell.
            target: Entity targeted, if any.

        Returns:
            Boolean whether the check passed.
        """
        if caster.effect_active("Ceasefire") and self.db.offensive:
            caster.msg("Can't use offensive abilities during a ceasefire!")
            return False

        # Mana or stamina cost
        for cost in self.db.cost:
            stat, amt = cost
            if caster.attributes.get(stat) < amt:
                caster.msg("Not enough " + stat.capitalize() + "!")
                return False

        # AP cost
        ap_cost = self.db.ap_cost or 2
        if caster.is_in_combat():
            current_ap = caster.db.combat_ap
        else:
            current_ap = COMBAT.get_ap(caster)
        if current_ap < ap_cost:
            caster.msg("Not enough AP!")
            return False

        # If ability has a cooldown
        if self.db.cooldown > 0 and not caster.is_superuser:
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

        # If ability is meant to target something
        if self.db.targeted:
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
        for stat, amt in self.db.cost:
            match stat:
                case "mana":
                    caster.db.mana -= amt
                case "stamina":
                    caster.db.stamina -= amt

        if caster.is_in_combat():
            caster.db.combat_turnhandler.spend_action(caster, self.db.ap_cost or 2, action_name="cast")

    def cast(self, caster: LivingEntity, target: Object = None):
        """
        If the ability's check passes, call the cooldown and cost adjuster, perform the ability, and spend the AP.
        :param caster: The entity casting the ability
        :param target: The target of the ability, if any
        :return: Bool whether the check passed and spell was successfully cast
        """
        if not self.check(caster, target):
            return False
        else:
            self.adjust_cooldowns_stats(caster)
            self.func(caster, target)
            return True

    def in_ability_tree(self, rpg_class):
        """
        Returns true if this ability is found in the given class's ability tree, i.e. if the given class can learn this
        ability through normal means.
        """
        ability_tree = rpg_class.ability_tree
        for level in ability_tree:
            if type(self) in ability_tree[level]:
                return True
        return False

    def color(self):
        return appearance.ability

    def cost_string(self):
        cost_string = ""
        for cost in self.db.cost:
            stat, amt = cost
            cost_string = cost_string + f"{amt} {stat}, "
        # Remove comma and space
        cost_string = cost_string[:-2]
        return cost_string

    def requires_string(self):
        string = ""
        for requirement in self.db.requires:
            stat, amt = requirement
            string = string + f"{amt} {stat.capitalize()}, "
        string = string[:-2]
        return string

    def get_help(self):
        """Formats help entries for individual abilities."""
        return f"""
        {self.get_display_name()}
        {self.desc}
        
        Requires: {self.requires_string()}
        Costs: {self.cost_string()}
        """


class SustainedAbility(Ability):
    def at_object_creation(self):
        super().at_object_creation()
        self.db.duration = None


class BowAbility(Ability):

    def check(self, caster, target):
        if not super().check(caster, target):
            return False

        if not isinstance(caster.db.equipment["primary"], Bow):  # If caster doesn't have a bow equipped
            caster.msg("You don't have a bow equipped!")
            return False
        return True
