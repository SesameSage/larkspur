from decimal import Decimal as Dec
from enum import Enum
from random import randint

from typeclasses.scripts.scripts import Script

# TODO: Increment effects more precisely on combat turn

EFFECT_SECS_PER_TURN = 5


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
    def __init__(self, effect_key: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.effect_key = effect_key

    def at_script_creation(self):
        self.db.effect_key = self.effect_key
        self.obj.db.effects[self.db.effect_key] = {}

    def at_script_delete(self):
        try:
            del self.obj.db.effects[self.db.effect_key]
        except KeyError:
            pass
        return True


class DurationEffect(EffectScript):
    def __init__(self, effect_key: str, duration: Dec, *args, **kwargs):
        super().__init__(effect_key=effect_key, *args, **kwargs)
        self.duration = duration

    def at_script_creation(self):
        super().at_script_creation()
        self.db.duration = self.duration
        self.db.seconds_passed = Dec(0)
        self.obj.db.effects[self.db.effect_key]["duration"] = self.db.duration
        self.obj.db.effects[self.db.effect_key]["seconds passed"] = 0

    def at_tick(self, **kwargs):
        if not self.db.duration:
            return
        if not self.obj.db.effects[self.db.effect_key]["seconds_passed"]:
            self.obj.db.effects[self.db.effect_key]["seconds_passed"] = 0
        if self.db.seconds_passed > self.db.duration:
            self.obj.location.msg_contents(f"{self.obj.get_display_name()}'s {self.db.effect_key} has worn off.")
            self.delete()
            return

        if not self.obj.is_in_combat():
            self.db.seconds_passed += Dec(1)
            self.obj.db.effects[self.db.effect_key]["seconds passed"] = self.db.seconds_passed


class PerSecEffect(DurationEffect):

    def __init__(self, effect_key: str, duration: Dec, range: tuple[int, int], *args, **kwargs):
        super().__init__(effect_key, duration, *args, **kwargs)
        self.range = range

    def at_script_creation(self):
        super().at_script_creation()
        self.db.range = self.range
        self.obj.db.effects[self.db.effect_key]["range"] = self.db.range

    def at_tick(self, **kwargs):
        super().at_tick(**kwargs)
        if not self.obj.is_in_combat():
            min, max = self.db.range
            amount = randint(min, max)
            self.increment(amount=amount, in_combat=False)

    def increment(self, amount: int, in_combat=False):
        pass


class Regeneration(PerSecEffect):
    def __init__(self, stat, range: tuple[int, int], duration: Dec, *args, **kwargs):
        super().__init__(effect_key=f"{stat.capitalize()} Regeneration", range=range, duration=duration, *args,
                         **kwargs)
        self.stat = stat

    def at_script_creation(self):
        super().at_script_creation()
        self.db.stat = self.stat
        self.db.key = "Regeneration"

    def increment(self, amount: int, in_combat=False):
        if in_combat:
            amount = amount * EFFECT_SECS_PER_TURN
            self.obj.location.msg_contents(f"{self.obj.get_display_name()} "
                                           f"recovers {amount} {self.stat} from regeneration.")

        match self.stat:
            case "health":
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
    def __init__(self, effect_key: str, range: tuple[int, int], duration: Dec, damage_type: DamageTypes, *args,
                 **kwargs):
        super().__init__(effect_key=effect_key, range=range, duration=duration, *args, **kwargs)
        self.damage_type = damage_type

    def at_script_creation(self):
        super().at_script_creation()
        self.db.damage_type = self.damage_type
        self.key = "DamageOverTime"

    def at_tick(self, **kwargs):
        super().at_tick(**kwargs)
        if self.obj.db.hp < 0:
            self.obj.db.hp = 0

    def increment(self, amount: int, in_combat=False):
        if in_combat:
            amount = amount * EFFECT_SECS_PER_TURN
            self.obj.location.msg_contents(f"{self.obj.get_display_name()} "
                                           f"takes {amount} damage from {self.db.effect_key}.")
        self.obj.apply_damage({self.db.damage_type: amount})


class FixedTimedEffect(DurationEffect):
    def __init__(self, effect_key: str, duration: Dec, *args, **kwargs):
        super().__init__(effect_key=effect_key, duration=duration, *args, **kwargs)

    def at_script_creation(self):
        super().at_script_creation()
        self.key = "Fixed Timed Effect"
        if hasattr(self, "amount"):
            self.obj.db.effects[self.db.effect_key]["amount"] = self.amount


class KnockedDown(FixedTimedEffect):
    # TODO: Knockdown
    def __init__(self, duration: Dec, *args, **kwargs):
        super().__init__(effect_key="Knocked Down", duration=duration, *args, **kwargs)

    def at_script_creation(self):
        super().at_script_creation()


class DamageMod(FixedTimedEffect):
    def __init__(self, effect_key: str, duration: Dec, damage_type: str, amount: int, *args, **kwargs):
        super().__init__(effect_key=effect_key, duration=duration, *args, **kwargs)
        self.damage_type = damage_type
        self.amount = amount

    def at_script_creation(self):
        super().at_script_creation()
        self.obj.db.effects[self.db.effect_key]["damage_type"] = self.damage_type


class AccuracyMod(FixedTimedEffect):
    def __init__(self, duration: Dec, amount: int, *args, **kwargs):
        if amount >= 0:
            effect_key = "Accuracy Up"
        else:
            effect_key = "Accuracy Down"
        super().__init__(effect_key, duration, *args, **kwargs)
        self.amount = amount


class DefenseMod(FixedTimedEffect):
    def __init__(self, duration: Dec, amount: int, *args, **kwargs):
        if amount > 0:
            effect_key = "Defense Up"
        else:
            effect_key = "Defense Down"
        super().__init__(effect_key, duration, *args, **kwargs)
        self.amount = amount


class EvasionMod(FixedTimedEffect):
    def __init__(self, duration: Dec, amount: int, *args, **kwargs):
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
