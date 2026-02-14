from random import randint

from combat.combat_constants import SECS_PER_TURN
from server import appearance
from typeclasses.scripts.scripts import Script

POSITIVE_EFFECTS = []
NEGATIVE_EFFECTS = ["Poisoned", "Burning", "Frozen", "Cursed", "KnockedDown"]
NEUTRAL_EFFECTS = ["Ceasefire"]


class EffectScript(Script):

    def at_script_creation(self):
        self.key = self.__class__.__name__
        self.db.source = None
        self.db.damage_type = None

    def pre_effect_add(self):
        """Called at the beginning of adding the effect to a target."""
        # Add dict entry on target's effects attribute
        self.obj.db.effects[self.db.effect_key] = {"source": self.db.source}
        if self.db.damage_type:
            self.obj.db.effects[self.db.effect_key]["damage_type"] = self.db.damage_type
        if self.db.amount:
            self.obj.db.effects[self.db.effect_key]["amount"] = self.db.amount

    def at_script_delete(self):
        # Remove entry from object's effects attributes, if still present
        try:
            del self.obj.db.effects[self.db.effect_key]
        except KeyError:
            pass
        return True

    def color(self):
        if "+" in self.key:
            return appearance.good_effect
        elif "-" in self.key:
            return appearance.bad_effect
        elif "Siphon" in self.key:
            return appearance.good_effect

        if self.key in POSITIVE_EFFECTS:
            return appearance.good_effect
        elif self.key in NEGATIVE_EFFECTS:
            return appearance.bad_effect
        elif self.key in NEUTRAL_EFFECTS:
            return appearance.effect
        return appearance.effect

    def reset_seconds(self, duration):
        pass


class DurationEffect(EffectScript):
    """An effect that lasts for a set number of seconds. In combat, 3 seconds pass per turn."""

    def pre_effect_add(self):
        """Called at the beginning of adding the effect to a target."""
        super().pre_effect_add()
        if not self.db.duration:
            self.db.duration = 3
        self.obj.db.effects[self.db.effect_key]["duration"] = self.db.duration
        self.db.seconds_passed = 0
        self.obj.db.effects[self.db.effect_key]["seconds passed"] = self.db.seconds_passed

    def apply(self, in_combat=False):
        """Increments the timer, checks if still active, and applies the effect."""
        self.add_seconds(in_combat=in_combat)
        self.check_duration()

    def add_seconds(self, amt=None, in_combat=False):
        """Increment the timer on how many seconds have passed since the effect was inflicted."""
        if not amt:
            amt = SECS_PER_TURN if in_combat else 1
        self.db.seconds_passed += amt
        self.obj.db.effects[self.db.effect_key]["seconds passed"] = self.db.seconds_passed

    def reset_seconds(self, duration):
        """
        Restarts the timer on an effect when re-inflicted while still active.
        Args:
            duration: Duration of new effect determined by cause
        """
        self.db.seconds_passed = 0
        self.db.duration = duration
        self.obj.db.effects[self.db.effect_key]["seconds passed"] = self.db.seconds_passed

    def check_duration(self):
        """Check if the effect has worn off, and remove if so."""
        effect_key = self.db.effect_key
        if self.db.seconds_passed >= self.db.duration:
            # Announce
            if effect_key not in ["Knocked Down"]:
                self.obj.location.msg_contents(
                    f"{self.obj.get_display_name(capital=True)}'s {self.color()}{effect_key}|n has worn off.")

            # Subtract amount from this script if the effect is stacking
            try:
                if self.obj.db.effects[effect_key]["amount"] > self.db.amount:
                    self.obj.db.effects[effect_key]["amount"] -= self.db.amount
            except KeyError:  # Isn't an effect with an amount
                pass

            # Delete other entities' Ceasefire scripts if Ceasefire is ending
            if self.db.effect_key == "Ceasefire":
                for entity in [content for content in self.obj.location.contents if content.attributes.has("hp")]:
                    script = entity.effect_active("Ceasefire")
                    if script:
                        script.delete()

            # Delete this script
            self.delete()


# <editor-fold desc="Stat modifier effects">
class StatMod(EffectScript):
    def pre_effect_add(self):
        super().pre_effect_add()
        if self.db.amount:
            try:
                self.obj.db.effects[self.db.effect_key]["amount"] += self.db.amount
            except KeyError:
                self.obj.db.effects[self.db.effect_key]["amount"] = self.db.amount
        if not self.attributes.has("stat"):
            self.db.stat = None

    def at_script_delete(self):
        # Remove entry from object's effects attributes, if still present
        try:
            if self.obj.db.effects[self.db.effect_key]["amount"] <= self.db.amount:
                del self.obj.db.effects[self.db.effect_key]
            else:
                self.obj.db.effects[self.db.effect_key] -= self.db.amount
        except KeyError:
            pass
        return True


class TimedStatMod(StatMod, DurationEffect):
    """Modifies a stat such as accuracy or defense for a set amount of time."""
    pass


# </editor-fold>

# <editor-fold desc="Per second effects">
class PerSecEffect(DurationEffect):
    """
    An effect that increments per second or every given number of seconds.

    Attributes:
        self.db.range (tuple): minimum and maximum amount to increment per second
    """

    def pre_effect_add(self):
        """Called at the beginning of adding the effect to a target."""
        super().pre_effect_add()
        if not self.db.range:
            self.db.range = (1, 1)
        self.obj.db.effects[self.db.effect_key]["range"] = self.db.range

        if not self.db.amount:
            self.db.amount = self.get_amount(self.obj.is_in_combat())
        self.obj.db.effects[self.db.effect_key]["amount"] = self.db.amount

    def apply(self, in_combat=False):
        """Increments the timer, checks if still active, and applies the effect."""
        self.increment(amount=self.get_amount(in_combat=in_combat), in_combat=in_combat)
        super().apply(in_combat)

    def get_amount(self, in_combat=False):
        min, max = self.db.range
        amount = randint(min, max)
        if in_combat:
            amount = amount * SECS_PER_TURN
        return amount

    def increment(self, amount: int, in_combat=False):
        """Applies an effect that changes a stat per second."""
        pass


class Regeneration(PerSecEffect):
    """Regenerate far more HP, mana, or stamina over time."""

    def pre_effect_add(self):
        """Called at the beginning of adding the effect to a target."""
        super().pre_effect_add()
        if not self.db.stat:
            self.db.stat = "HP"
        self.db.effect_key = "Regenerating " + self.db.stat.capitalize()
        self.obj.db.effects[self.db.effect_key]["stat"] = self.db.stat

    def increment(self, amount: int, in_combat=False):
        """Increase the stat by the given amount."""
        if in_combat:
            self.obj.location.msg_contents(f"{self.obj.get_display_name(capital=True)} "
                                           f"recovers {amount} {self.db.stat} from regeneration.")

        match self.db.stat:
            case "HP":
                self.obj.db.hp += amount
            case "mana":
                self.obj.db.mana += amount
            case "stamina":
                self.obj.db.stamina += amount
        self.obj.cap_stats()


class Drain(PerSecEffect):
    """Lose stamina or mana over time."""

    def pre_effect_add(self):
        super().pre_effect_add()
        if not self.db.stat:
            self.db.stat = "mana"
        stat = self.db.stat
        self.db.effect_key = stat.capitalize() + " Drain"
        self.obj.db.effects[self.db.effect_key]["stat"] = stat

    def increment(self, amount: int, in_combat=False):
        """Decrease the script's associated stat by the given amount."""
        match self.db.stat:
            case "mana":
                self.obj.db.mana -= amount
            case "stamina":
                self.obj.db.stamina -= amount
        self.obj.cap_stats()
        if in_combat:
            self.obj.location.msg_contents(
                f"{self.obj.get_display_name(capital=True)} is drained of {amount} {self.db.stat}.")


class DamageOverTime(PerSecEffect):
    """
    Damages the user per second.

        Attributes:
            self.db.damage_type (DamageType): Type of damage to deal
    """

    def increment(self, amount: int, in_combat=False):
        """Apply the damages."""
        if in_combat:
            self.obj.location.msg_contents(f"{self.obj.get_display_name(capital=True)} takes "
                                           f"{appearance.dmg_color(self.obj)}{amount} damage|n from "
                                           f"{self.color()}{self.db.effect_key}.")
        self.obj.db.hp -= amount
        self.obj.check_zero_hp()


class Burning(DamageOverTime):
    fixed_attributes = [
        ("effect_key", "Burning")
    ]

    def pre_effect_add(self):
        super().pre_effect_add()
        if self.obj.effect_active("Frozen"):
            self.obj.location.msg_contents(f"{self.obj.get_display_name()} thaws out!")
            self.obj.scripts.get("Frozen")[0].delete()


class Poisoned(DamageOverTime):
    fixed_attributes = [
        ("effect_key", "Poisoned")
    ]


# </editor-fold>


class KnockedDown(DurationEffect):
    """Lose a turn standing back up, and take 50% damage for that turn."""
    fixed_attributes = [
        ("effect_key", "Knocked Down"),
        ("duration", 2 * SECS_PER_TURN)  # Always lasts 2 turns
    ]


class Frozen(DurationEffect):
    """Can’t attack, cast, or use items. Quickened by fire damage, cancelled by burning."""
    fixed_attributes = [
        ("effect_key", "Frozen")
    ]

