from enum import Enum
from random import randint

from server import appearance
from typeclasses.scripts.scripts import Script

EFFECT_SECS_PER_TURN = 3


class DamageTypes(Enum):
    BLUNT = 1
    SLASHING = 2
    PIERCING = 3
    FIRE = 4
    COLD = 5
    SHOCK = 6
    POISON = 7

    def get_display_name(self, capital=False):
        name = self.name.lower()
        if capital:
            name = name.capitalize()
        return name


class EffectScript(Script):

    def color(self):
        return appearance.effect

    def pre_effect_add(self):
        self.obj.db.effects[self.db.effect_key] = {}

    def at_script_delete(self):
        try:
            del self.obj.db.effects[self.db.effect_key]
        except KeyError:
            pass
        return True

    def reset_seconds(self, duration):
        pass


class DurationEffect(EffectScript):

    def pre_effect_add(self):
        super().pre_effect_add()
        if not self.db.duration:
            self.db.duration = 3
        self.obj.db.effects[self.db.effect_key]["duration"] = self.db.duration
        self.db.seconds_passed = 0
        self.obj.db.effects[self.db.effect_key]["seconds passed"] = self.db.seconds_passed

    def apply(self, in_combat=False):
        self.add_seconds(in_combat=in_combat)
        self.check_duration()

    def add_seconds(self, in_combat=False):
        self.db.seconds_passed += (EFFECT_SECS_PER_TURN if in_combat else 1)
        self.obj.db.effects[self.db.effect_key]["seconds passed"] = self.db.seconds_passed

    def reset_seconds(self, duration):
        self.db.seconds_passed = 0
        if duration > self.db.duration:
            self.db.duration = duration
        self.obj.db.effects[self.db.effect_key]["seconds passed"] = self.db.seconds_passed

    def check_duration(self):
        if self.db.seconds_passed >= self.db.duration:
            if self.db.effect_key not in ["Knocked Down"]:
                self.obj.location.msg_contents(f"{self.obj.get_display_name()}'s {self.color()}{self.db.effect_key}|n has worn off.")
            self.delete()


class PerSecEffect(DurationEffect):

    def pre_effect_add(self):
        super().pre_effect_add()
        if not self.db.range:
            self.db.range = (1, 1)
        self.obj.db.effects[self.db.effect_key]["range"] = self.db.range

    def apply(self, in_combat=False):
        self.increment(amount=self.get_amount(in_combat=in_combat), in_combat=in_combat)
        self.add_seconds(in_combat=in_combat)
        self.check_duration()

    def get_amount(self, in_combat=False):
        min, max = self.db.range
        amount = randint(min, max)
        if in_combat:
            amount = amount * EFFECT_SECS_PER_TURN
        return amount

    def increment(self, amount: int, in_combat=False):
        pass


class Regeneration(PerSecEffect):

    def pre_effect_add(self):
        super().pre_effect_add()
        if not self.db.stat:
            self.db.stat = "HP"
        self.db.effect_key = "Regenerating " + self.db.stat
        self.obj.db.effects[self.db.effect_key]["stat"] = self.db.stat

    def increment(self, amount: int, in_combat=False):
        if in_combat:
            self.obj.location.msg_contents(f"{self.obj.get_display_name()} "
                                           f"recovers {amount} {self.db.stat} from regeneration.")

        match self.db.stat:
            case "HP":
                self.obj.db.hp += amount
                if self.obj.db.hp > self.obj.db.max_hp:
                    self.obj.db.hp = self.obj.db.max_hp
            case "mana":
                self.obj.db.mana += amount
                if self.obj.db.mana > self.obj.db.max_mana:
                    self.obj.db.mana = self.obj.db.max_mana
            case "stamina":
                self.obj.db.stamina += amount
                if self.obj.db.stamina > self.obj.db.max_stamina:
                    self.obj.db.stamina = self.obj.db.max_stamina


class DamageOverTime(PerSecEffect):

    def pre_effect_add(self):
        super().pre_effect_add()
        if not self.db.damage_type:
            self.db.damage_type = DamageTypes.POISON

    def increment(self, amount: int, in_combat=False):
        if in_combat:
            self.obj.location.msg_contents(f"{self.obj.get_display_name()} "
                                           f"takes {appearance.dmg_color(None, self.obj)}{amount} damage|n from {self.color()}{self.db.effect_key}.")
        self.obj.apply_damage({self.db.damage_type: amount})


class DurationMod(DurationEffect):

    def pre_effect_add(self):
        super().pre_effect_add()
        self.key = "Fixed Timed Effect"
        if hasattr(self, "amount"):
            self.obj.db.effects[self.db.effect_key]["amount"] = self.amount


class KnockedDown(DurationEffect):
    # Lose 2 turns getting up
    def pre_effect_add(self):
        super().pre_effect_add()
        self.db.effect_key = "Knocked Down"
        self.db.duration = 2 * EFFECT_SECS_PER_TURN  # Always lasts 2 turns


class DamageMod(DurationMod):
    def __init__(self, effect_key: str, duration: int, damage_type: str, amount: int, *args, **kwargs):
        super().__init__(effect_key=effect_key, duration=duration, *args, **kwargs)
        self.damage_type = damage_type
        self.amount = amount

    def at_script_creation(self):
        super().at_script_creation()
        self.obj.db.effects[self.db.effect_key]["damage_type"] = self.damage_type


class AccuracyMod(DurationMod):
    def __init__(self, duration: int, amount: int, *args, **kwargs):
        if amount >= 0:
            effect_key = "Accuracy Up"
        else:
            effect_key = "Accuracy Down"
        super().__init__(effect_key, duration, *args, **kwargs)
        self.amount = amount


class DefenseMod(DurationMod):
    def __init__(self, duration: int, amount: int, *args, **kwargs):
        if amount > 0:
            effect_key = "Defense Up"
        else:
            effect_key = "Defense Down"
        super().__init__(effect_key, duration, *args, **kwargs)
        self.amount = amount


class EvasionMod(DurationMod):
    def __init__(self, duration: int, amount: int, *args, **kwargs):
        if amount > 0:
            effect_key = "Evasion Up"
        else:
            effect_key = "Evasion Down"
        super().__init__(effect_key, duration, *args, **kwargs)
        self.amount = amount


"""
----------------------------------------------------------------------------
PROTOTYPES START HERE
----------------------------------------------------------------------------

You can paste these prototypes into your game's prototypes.py module in your
/world/ folder, and use the spawner to create them - they serve as examples
of items you can make and a handy way to demonstrate the system for
conditions as well.

Items don't have any particular typeclass - any object with a db entry
"item_func" that references one of the functions given above can be used as
an item with the 'use' command.

Only "item_func" is required, but item behavior can be further modified by
specifying any of the following:

    item_uses (int): If defined, item has a limited number of uses

    item_selfonly (bool): If True, user can only use the item on themself

    item_consumable(True or str): If True, item is destroyed when it runs
        out of uses. If a string is given, the item will spawn a new
        object as it's destroyed, with the string specifying what prototype
        to spawn.

    item_kwargs (dict): Keyword arguments to pass to the function defined in
        item_func. Unique to each function, and can be used to make multiple
        items using the same function work differently.
"""
MEDKIT = {
    "key": "a medical kit",
    "aliases": ["medkit"],
    "desc": "A standard medical kit. It can be used a few times to heal wounds.",
    "item_func": "heal",
    "item_uses": 3,
    "item_consumable": True,
    "item_kwargs": {"healing_range": (15, 25)},
}

GLASS_BOTTLE = {"key": "a glass bottle", "desc": "An empty glass bottle."}

HEALTH_POTION = {
    "key": "a health potion",
    "desc": "A glass bottle full of a mystical potion that heals wounds when used.",
    "item_func": "heal",
    "item_uses": 1,
    "item_consumable": "GLASS_BOTTLE",
    "item_kwargs": {"healing_range": (35, 50)},
}

REGEN_POTION = {
    "key": "a regeneration potion",
    "desc": "A glass bottle full of a mystical potion that regenerates wounds over time.",
    "item_func": "add_condition",
    "item_uses": 1,
    "item_consumable": "GLASS_BOTTLE",
    "item_kwargs": {"conditions": [("Regeneration", 10)]},
}

HASTE_POTION = {
    "key": "a haste potion",
    "desc": "A glass bottle full of a mystical potion that hastens its user.",
    "item_func": "add_condition",
    "item_uses": 1,
    "item_consumable": "GLASS_BOTTLE",
    "item_kwargs": {"conditions": [("Haste", 10)]},
}

BOMB = {
    "key": "a rotund bomb",
    "desc": "A large black sphere with a fuse at the end. Can be used on enemies in combat.",
    "item_func": "attack",
    "item_uses": 1,
    "item_consumable": True,
    "item_kwargs": {"damage_range": (25, 40), "accuracy": 25},
}

TASER = {
    "key": "a taser",
    "desc": "A device that can be used to paralyze enemies in combat.",
    "item_func": "attack",
    "item_kwargs": {
        "damage_range": (10, 20),
        "accuracy": 0,
        "inflict_condition": [("Paralyzed", 1)],
    },
}

GHOST_GUN = {
    "key": "a ghost gun",
    "desc": "A gun that fires scary ghosts at people. Anyone hit by a ghost becomes frightened.",
    "item_func": "attack",
    "item_uses": 6,
    "item_kwargs": {
        "damage_range": (5, 10),
        "accuracy": 15,
        "inflict_condition": [("Frightened", 1)],
    },
}

ANTIDOTE_POTION = {
    "key": "an antidote potion",
    "desc": "A glass bottle full of a mystical potion that cures poison when used.",
    "item_func": "cure_condition",
    "item_uses": 1,
    "item_consumable": "GLASS_BOTTLE",
    "item_kwargs": {"to_cure": ["Poisoned"]},
}

AMULET_OF_MIGHT = {
    "key": "The Amulet of Might",
    "desc": "The one who holds this amulet can call upon its power to gain great strength.",
    "item_func": "add_condition",
    "item_selfonly": True,
    "item_kwargs": {"conditions": [("Damage Up", 3), ("Accuracy Up", 3), ("Defense Up", 3)]},
}

AMULET_OF_WEAKNESS = {
    "key": "The Amulet of Weakness",
    "desc": "The one who holds this amulet can call upon its power to gain great weakness. "
            "It's not a terribly useful artifact.",
    "item_func": "add_condition",
    "item_selfonly": True,
    "item_kwargs": {"conditions": [("Damage Down", 3), ("Accuracy Down", 3), ("Defense Down", 3)]},
}
