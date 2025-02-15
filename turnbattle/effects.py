from enum import Enum
from random import randint

from typeclasses.scripts.scripts import Script

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


REGEN_RATE = (4, 8)  # Min and max HP regen for Regeneration
POISON_RATE = (4, 8)  # Min and max damage for Poisoned
ACC_UP_MOD = 25  # Accuracy Up attack roll bonus
ACC_DOWN_MOD = -25  # Accuracy Down attack roll penalty
DMG_UP_MOD = 5  # Damage Up damage roll bonus
DMG_DOWN_MOD = -5  # Damage Down damage roll penalty
DEF_UP_MOD = 15  # Defense Up defense bonus
DEF_DOWN_MOD = -15  # Defense Down defense penalty


class EffectScript(Script):
    def __init__(self, effect_key: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.effect_key = effect_key

    def at_script_creation(self):
        self.obj.db.effects[self.effect_key] = {}

    def at_script_delete(self):
        del self.obj.db.effects[self.effect_key]
        return True


class DurationEffect(EffectScript):
    def __init__(self, effect_key: str, duration: int, *args, **kwargs):
        super().__init__(effect_key=effect_key, *args, **kwargs)
        self.duration = duration

    def at_script_creation(self):
        super().at_script_creation()
        self.interval = 1
        self.obj.db.effects[self.effect_key] = {"duration": self.duration}
        self.seconds_passed = 0

    def at_repeat(self, **kwargs):
        if self.seconds_passed > self.duration:
            self.obj.location.msg_contents(f"{self.obj.get_display_name()}'s {self.effect_key.lower()} has worn off.")
            self.delete()
            return


class PerSecEffect(DurationEffect):

    def __init__(self, effect_key: str, duration: int, range: tuple[int, int], *args, **kwargs):
        super().__init__(effect_key, duration, *args, **kwargs)
        self.range = range

    def at_script_creation(self):
        super().at_script_creation()
        self.applied_this_turn = False

    def at_repeat(self, **kwargs):
        super().at_repeat()
        min, max = self.range
        amount = randint(min, max)
        if hasattr(self.obj, "rules") and self.obj.rules.is_in_combat(self.obj):
            if self.obj.rules.is_turn(self.obj):
                if not self.applied_this_turn:
                    self.increment(amount=amount, in_combat=True)
                    self.seconds_passed += EFFECT_SECS_PER_TURN
                    self.applied_this_turn = True
            else:
                self.applied_this_turn = False
        else:  # Not in combat
            self.applied_this_turn = False
            self.increment(amount=amount, in_combat=False)
            self.seconds_passed += 1

    def increment(self, amount: int, in_combat=False):
        pass


class Regeneration(PerSecEffect):
    def __init__(self, range: tuple[int, int], duration: int, *args, **kwargs):
        super().__init__(effect_key="Regeneration", range=range, duration=duration, *args, **kwargs)

    def at_script_creation(self):
        super().at_script_creation()
        self.key = "Regeneration"
        self.healed_this_turn = False

    def at_repeat(self, **kwargs):
        super().at_repeat()  # Checks for duration end of all effect scripts
        if self.obj.db.hp > self.obj.db.max_hp:
            self.obj.db.hp = self.obj.db.max_hp

    def increment(self, amount: int, in_combat=False):
        if in_combat:
            amount = amount * EFFECT_SECS_PER_TURN
            self.obj.location.msg_contents(f"{self.obj.get_display_name()} "
                                           f"recovers {amount} HP from regeneration.")

        self.obj.db.hp += amount


class DamageOverTime(PerSecEffect):
    def __init__(self, effect_key: str, range:tuple[int, int], duration: int, damage_type: DamageTypes, *args,
                 **kwargs):
        super().__init__(effect_key=effect_key, range=range, duration=duration, *args, **kwargs)
        self.damage_type = damage_type

    def at_script_creation(self):
        super().at_script_creation()
        self.key = "Damage Over Time"
        self.interval = 1
        self.damaged_this_turn = False

    def at_repeat(self, **kwargs):
        super().at_repeat()
        if self.obj.db.hp < 0:
            self.obj.db.hp = 0

    def increment(self, amount: int, in_combat=False):
        if in_combat:
            amount = amount * EFFECT_SECS_PER_TURN
            self.obj.location.msg_contents(f"{self.obj.get_display_name()} "
                                           f"takes {amount} damage from {self.effect_key}.")
        self.obj.db.hp -= amount


class FixedModWithDuration(DurationEffect):
    def __init__(self, duration: int, effect_key: str, *args, **kwargs):
        super().__init__(duration=duration, effect_key=effect_key, *args, **kwargs)

    def at_script_creation(self):
        super().at_script_creation()
        self.key = "Timed Mod"
        self.interval = 1
        self.incremented_this_turn = False

    def at_repeat(self, **kwargs):
        super().at_repeat()
        if hasattr(self.obj, "rules") and self.obj.rules.is_in_combat(self.obj):
            if self.obj.rules.is_turn(self.obj):
                if not self.incremented_this_turn:
                    self.seconds_passed += EFFECT_SECS_PER_TURN
            else:
                self.incremented_this_turn = False
        else:
            self.seconds_passed += 1


effect_callers = {
    "Regeneration"
}

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
