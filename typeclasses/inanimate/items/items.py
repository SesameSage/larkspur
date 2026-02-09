from decimal import Decimal as Dec
from random import randint

from evennia import EvTable
from evennia.utils import inherits_from

from combat import effects
from combat.effects import DamageTypes, EffectScript
from server import appearance
from typeclasses.base.objects import Object


def itemfunc_heal(item, user, target, **kwargs):
    """
    Item function that heals HP.

    kwargs:
        min_healing(int): Minimum amount of HP recovered
        max_healing(int): Maximum amount of HP recovered
    """
    if not target:
        target = user  # Target user if none specified

    if not target.attributes.has("max_hp"):  # Has no HP to speak of
        user.msg("You can't use %s on that." % item)
        return False  # Returning false aborts the item use

    if target.db.hp >= target.get_max("hp"):
        user.msg("%s is already at full health." % target)
        return False

    # Retrieve healing range from kwargs, if present
    if "range" in kwargs:
        min_healing = kwargs["range"][0]
        max_healing = kwargs["range"][1]

    amt_to_heal = randint(min_healing, max_healing)
    target.db.hp += amt_to_heal
    target.cap_stats()

    user_name = user.get_display_name(capital=True)
    user.location.msg_contents(
        "%s uses %s! %s regains %i HP!" % (
            user_name, item.get_display_name(article=True), user_name, amt_to_heal))


def itemfunc_restore_mana(item, user, target, **kwargs):
    """
    Item function that restores mana.

    kwargs:
        min_recovered(int): Minimum amount of mana recovered
        max_recovered(int): Maximum amount of mana recovered
    """
    if not target:
        target = user  # Target user if none specified

    if not target.attributes.has("max_mana"):  # Has no mana to speak of
        user.msg("You can't use %s on that." % item)
        return False  # Returning false aborts the item use

    if target.db.mana >= target.get_max("mana"):
        user.msg("%s is already at full health." % target)
        return False

    # Retrieve healing range from kwargs, if present
    if "range" in kwargs:
        min_recovered = kwargs["range"][0]
        max_recovered = kwargs["range"][1]

    amt_to_recover = randint(min_recovered, max_recovered)
    target.db.mana += amt_to_recover
    target.cap_stats()

    user_name = user.get_display_name(capital=True)
    user.location.msg_contents(
        "%s uses %s! %s regains %i mana!" % (
            user_name, item.get_display_name(article=True), user_name, amt_to_recover))


def itemfunc_restore_stamina(item, user, target, **kwargs):
    """
    Item function that restores stamina.

    kwargs:
        min_recovered(int): Minimum amount of stamina recovered
        max_recovered(int): Maximum amount of stamina recovered
    """
    if not target:
        target = user  # Target user if none specified

    if not target.attributes.has("max_stam"):  # Has no mana to speak of
        user.msg("You can't use %s on that." % item)
        return False  # Returning false aborts the item use

    if target.db.stamina >= target.db.max_stam:
        user.msg("%s is already at full health." % target)
        return False

    # Retrieve healing range from kwargs, if present
    if "range" in kwargs:
        min_recovered = kwargs["range"][0]
        max_recovered = kwargs["range"][1]

    amt_to_recover = randint(min_recovered, max_recovered)
    target.db.stamina += amt_to_recover
    target.cap_stats()

    user_name = user.get_display_name(capital=True)
    user.location.msg_contents(
        "%s uses %s! %s regains %i stamina!" % (
            user_name, item.get_display_name(article=True), user_name, amt_to_recover))


def itemfunc_add_effect(item, user, target, **kwargs):
    """
    Item function that gives the target one or more conditions.

    kwargs:
        effects (list): Conditions added by the item
           formatted as a list of tuples: (condition (str), duration (int or True))

    Notes:
        Should mostly be used for beneficial conditions - use itemfunc_attack
        for an item that can give an enemy a harmful condition.
    """
    item_effects = []

    if not target:
        target = user  # Target user if none specified

    if not target.attributes.has("max_hp"):  # Is not a fighter
        user.msg("You can't use %s on that." % item)
        return False  # Returning false aborts the item use

    if target.db.combat_turnhandler.db.grid.distance(user, target) > kwargs["range"]:
        user.msg("Out of range for this item!")
        return False

    # Retrieve condition / duration from kwargs, if present
    if "effects" in kwargs:
        item_effects = kwargs["effects"]

    user.location.msg_contents(
        "%s uses %s!" % (user.get_display_name(capital=True), item.get_display_name(article=True)))

    # Add conditions to the target
    attr_list = []
    for effect in item_effects:
        for entry in effect.items():
            if entry[0] != "script_key":
                attr_list.append(entry)
        effect_script = getattr(effects, effect["script_key"])
        attr_list.append(("source", item.get_display_name()))
        target.add_effect(typeclass=effect_script, attributes=attr_list, stack=True)

    return True


def itemfunc_cure_condition(item, user, target, **kwargs):
    if not target:
        target = user  # Target user if none specified

    if not target.attributes.has("max_hp"):  # Is not a fighter
        user.msg("You can't use %s on that." % item.get_display_name())
        return False  # Returning false aborts the item use

    if "effects_cured" in kwargs:
        effects_cured = kwargs["effects_cured"]

    user.location.msg_contents(
        "%s uses %s! " % (user.get_display_name(capital=True), item.get_display_name(article=True)))

    for script in target.scripts.all():
        if inherits_from(script, EffectScript):
            effect_key = script.db.effect_key
            if effect_key in effects_cured:
                script.delete()
                user.location.msg_contents(f"{target} is no longer {script.color()}{effect_key}.")


def itemfunc_attack(item, user, target, **kwargs):
    """
    Item function that attacks a target.

    kwargs:
        min_damage(int): Minimum damage dealt by the attack
        max_damage(int): Maximum damage dealth by the attack
        accuracy(int): Bonus / penalty to attack accuracy roll
        effects_inflicted(list): List of conditions inflicted on hit,
            formatted as a (str, int) tuple containing condition name
            and duration.

    Notes:
        Calls resolve_attack at the end.
    """
    if not user.is_in_combat():
        user.msg("You can only use that in combat.")
        return False  # Returning false aborts the item use

    if not target:
        user.msg("You have to specify a target to use %s! (use <item> = <target>)" % item)
        return False

    if target == user:
        user.msg("You can't attack yourself!")
        return False

    if not target.db.hp:  # Has no HP
        user.msg("You can't use %s on that." % item)
        return False

    damage_ranges = {}
    accuracy = 0
    effects_inflicted = []

    # Retrieve values from kwargs, if present
    if "damage_ranges" in kwargs:
        for type_name in kwargs:
            try:
                damage_type = DamageTypes[type_name]
            except KeyError:
                user.msg(appearance.warning + "No damage type matching for " + type_name)
                return
            damage_ranges[damage_type] = kwargs["damage_ranges"][type_name]

    if "accuracy" in kwargs:
        accuracy = kwargs["accuracy"]
    # if "effects_inflicted" in kwargs:
    #     effects_inflicted = kwargs["effects_inflicted"]

    # Roll attack and damage
    attack_value = randint(1, 100) + accuracy
    # TODO: Itemfunc Attack

    # Account for "Accuracy Up" and "Accuracy Down" conditions
    if "Accuracy Up" in user.db.effects:
        attack_value += 25
    if "Blinded" in user.db.effects:
        attack_value -= attack_value / 2

    user.location.msg_contents("%s attacks %s with %s!" % (user, target, item))
    user.db.combat_turnhandler.resolve_attack(
        user,
        target,
        accuracy=attack_value,
        damage_values=damage_ranges,
        inflict_condition=effects_inflicted,
    )


ITEMFUNCS = {
    "heal": itemfunc_heal,
    "attack": itemfunc_attack,
    "add_effect": itemfunc_add_effect,
    "cure_condition": itemfunc_cure_condition,
    "restore_mana": itemfunc_restore_mana,
    "restore_stamina": itemfunc_restore_stamina,
}


class Item(Object):

    def at_object_creation(self):
        super().at_object_creation()
        self.db.desc = "This is an item."
        self.db.weight = Dec(0)
        self.db.avg_value = 0.0
        self.db.range = 0

        self.db.quest_hooks = {"at_get": {}, "at_give": {}}

    def color(self):
        return appearance.item

    def identify(self):
        """Return a table containing details on the item such as its stats and effects."""
        table = EvTable(self.get_display_name(), (self.color() + self.__class__.__name__), pretty_corners=True)
        table.add_row(f"Weight: {self.db.weight}")
        table.add_row(f"Average value: {appearance.gold}{self.db.avg_value}|n")
        return table

    def at_get(self, getter, **kwargs):
        super().at_get(getter, **kwargs)
        hooks = self.db.quest_hooks["at_get"]
        for qid in hooks:
            for stage in hooks[qid]:
                hook_data = hooks[qid][stage]
                if getter.attributes.has("quest_stages") and getter.quests.at_stage(qid, stage):
                    getter.msg(hook_data["msg"])
                    getter.quests.advance_quest(hook_data["next_stage"])

    def at_give(self, giver, getter, **kwargs):
        super().at_give(giver, getter, **kwargs)
        hooks = self.db.quest_hooks["at_give"]
        for qid in hooks:
            for stage in hooks[qid]:
                hook_data = hooks[qid][stage]
                if getter.attributes.has("quest_stages") and getter.quests.at_stage(qid, stage):
                    getter.msg(hook_data["msg"])
                    getter.quests.advance_quest(hook_data["next_stage"])


class LightItem(Item):
    """An item that provides light."""

    def at_object_creation(self):
        super().at_object_creation()
        self.db.desc = "An item that provides light."
