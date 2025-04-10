from random import randint

from evennia.prototypes.spawner import spawn

from server import appearance
from server.appearance import dmg_color
from combat.effects import DamageTypes
from typeclasses.inanimate.items.items import ITEMFUNCS
from typeclasses.inanimate.items.usables import Consumable


class CombatHandler:

    def get_attack(self, attacker, defender):
        """
        Returns an accuracy for an attack, applying only the attacker's stat modifications to a hitroll.

        Args:
            attacker (obj): Character doing the attacking
            defender (obj): Character being attacked

        Returns:
            attack_value (int): Accuracy value to be compared against a defense value
                to determine whether an attack hits or misses.
        """
        # Start with a roll from 1 to 100.
        attack_value = randint(1, 100)
        attacker.location.more_info(f"Hitroll {attack_value} ({attacker.name})")
        accuracy_bonus = 0
        # If armed, add weapon's accuracy bonus.
        weapon = attacker.get_weapon()
        if weapon:
            accuracy_bonus += weapon.db.accuracy_bonus
            attacker.location.more_info(f"+{accuracy_bonus} accuracy from {weapon.name} ({attacker.name})")
        attack_value += accuracy_bonus

        # Apply attacker's hitroll buffs and debuffs.
        buff = 0
        if "Accuracy Up" in attacker.db.effects:
            buff += attacker.db.effects["Accuracy Up"]["amount"]
        if "Blinded" in attacker.db.effects:
            buff -= (attack_value) // 2
            attacker.location.more_info("-50% accuracy from Blinded")
        attack_value += buff

        attacker.location.more_info(f"{attack_value} to hit ({attacker.name})")
        return attack_value

    def get_damage(self, attacker, defender):
        """
        Returns a value for damage to be deducted from the defender's HP after abilities
        successful hit.

        Args:
            attacker (obj): Character doing the attacking
            defender (obj): Character being damaged

        Returns:
            damage_values (dict): Damage types and values, which is to be deducted from the defending
                character's HP.
        """
        damage_values = {}
        # Generate a damage value from wielded weapon if armed
        weapon = attacker.get_weapon()
        if weapon:
            for damage_type in weapon.db.damage_ranges:
                # Roll between minimum and maximum damage
                values = weapon.db.damage_ranges[damage_type]
                damage_values[damage_type] = randint(values[0], values[1])
                attacker.location.more_info(
                    f"+{damage_values[damage_type]} {damage_type.get_display_name()} damage from {weapon.name} ({attacker.name})")
                # Make sure minimum damage is 0
                if damage_values[damage_type] < 0:
                    damage_values[damage_type] = 0

        # If not armed, use unarmed damage
        else:
            damage_values[DamageTypes.BLUNT] = randint(
                attacker.db.unarmed_damage_range[0], attacker.db.unarmed_damage_range[1]
            )

        attacker.location.more_info(f"Damage roll ({attacker.name}):")
        attacker.location.more_info(str([f"{damage_type.get_display_name()}: {damage_values[damage_type]}"
                                         for damage_type in damage_values]))

        # Apply attacker's relevant effects
        if "Damage Up" in attacker.db.effects:
            damage_boost = attacker.db.effects["Damage Up"]["amount"]
            for damage_type in damage_values:
                damage_values[damage_type] += damage_boost
                attacker.location.more_info(f"+{damage_boost} {damage_type} damage from effect ({attacker.name})")
        if "Damage Down" in attacker.db.effects:
            damage_penalty = attacker.db.effects["Damage Down"]["amount"]
            for damage_type in damage_values:
                damage_values[damage_type] -= damage_penalty
                attacker.location.more_info(f"-{damage_penalty} {damage_type} damage from effect ({attacker.name}")

        # Apply defender's relevant effects
        if defender.effect_active("Knocked Down"):
            # Add 50% to damage
            defender.location.more_info("+50% damage (Knocked Down)")
            for damage_type in damage_values:
                damage_values[damage_type] += damage_values[damage_type] // 2

        # If defender is armored, reduce incoming damage
        for damage_type in damage_values:
            damage_values[damage_type] -= defender.get_defense()

        return damage_values

    def resolve_attack(
            self,
            attacker,
            defender,
            attack_value=None,
            evasion_value=None,
            damage_values=None,
            inflict_condition=[],
    ):
        """
               Resolves an attack and outputs the result.

               Args:
                   attacker (obj): Character doing the attacking
                   defender (obj): Character being attacked

               Options:
                   attack_value (int): Override for attack roll
                   evasion_value (int): Override for evasion value
                   damage_value (int): Override for damage value
                   inflict_condition (list): Conditions to inflict upon hit, a
                       list of tuples formated as (condition(str), duration(int))

               Notes:
                   This function is called by normal attacks as well as attacks
                   made with items.
               """
        # Get the attacker's weapon type to reference in combat messages.
        attackers_weapon = attacker.db.unarmed_attack
        if attacker.db.equipment["primary"]:
            weapon = attacker.db.equipment["primary"]
            attackers_weapon = weapon.get_display_name()

        # Get an attack roll from the attacker.
        if not attack_value:
            attack_value = self.get_attack(attacker, defender)

        # Get an evasion value from the defender.
        if not evasion_value:
            evasion_value = defender.get_evasion()

        # If the attack value is lower than the defense value, miss. Otherwise, hit.
        if attack_value < evasion_value:
            attacker.location.more_info(f"{attack_value} hit < {evasion_value} evasion (miss)")
            attacker.location.msg_contents(
                "%s's %s misses %s!" % (attacker.get_display_name(), attackers_weapon, defender.get_display_name())
            )

        else:
            attacker.location.more_info(f"{attack_value} hit > {evasion_value} evasion (success)")

            damage_values = self.get_damage(attacker, defender)
            damage_values = {key: value for key, value in damage_values.items() if value > 0}

            msg = "%s's %s strikes %s for " % (
                attacker.get_display_name(), attackers_weapon, defender.get_display_name())

            if bool(damage_values):  # If any damages are > 0
                for i, damage_type in enumerate(damage_values):
                    if i == len(damage_values) - 1 and len(damage_values) > 1:  # If at the last damage type to list
                        if msg[-1] != " ":
                            msg = msg + " "
                        msg = msg + "and "
                    elif len(damage_values) > 2:  # If there are more to list
                        msg = msg + ", "
                    msg = msg + f"{dmg_color(attacker, defender)}{damage_values[damage_type]} {damage_type.get_display_name()}|n"

                msg = msg + f"{dmg_color(attacker, defender)} damage!|n"
                attacker.location.msg_contents(msg)
            else:  # No damage dealt
                attacker.location.msg_contents(
                    "%s's %s bounces harmlessly off %s!" % (
                        attacker.get_display_name(), attackers_weapon, defender.get_display_name())
                )

            defender.apply_damage(damage_values)
            """# Inflict conditions on hit, if any specified
            for condition in inflict_condition:
                self.add_effect(defender, attacker, condition[0], condition[1])"""

    # ITEM RULES

    def spend_item_use(self, item, user):
        """
        Spends one use on an item with limited uses.

        Args:
            item (obj): Item being used
            user (obj): Character using the item

        Notes:
            If item.db.item_consumable is 'True', the item is destroyed if it
            runs out of uses - if it's a string instead of 'True', it will also
            spawn a new object as residue, using the value of item.db.item_consumable
            as the name of the prototype to spawn.
        """
        item.db.item_uses -= 1  # Spend one use

        if item.db.item_uses > 0:  # Has uses remaining
            # Inform the player
            user.msg("%s has %i uses remaining." % (item.key.capitalize(), item.db.item_uses))

        else:  # All uses spent
            if not isinstance(item, Consumable):  # Item isn't consumable
                # Just inform the player that the uses are gone
                user.msg("%s has no uses remaining." % item.key.capitalize())

            else:  # If item is consumable
                # If the value is 'True', just destroy the item
                if isinstance(item, Consumable):
                    user.msg("%s has been consumed." % item.get_display_name(capital=True))
                    item.delete()  # Delete the spent item

                else:  # If a string, use value of item_consumable to spawn an object in its place
                    residue = spawn({"prototype": item.db.item_consumable})[0]  # Spawn the residue
                    # Move the residue to the same place as the item
                    residue.location = item.location
                    user.msg("After using %s, you are left with %s." % (item, residue))
                    item.delete()  # Delete the spent item

    def use_item(self, user, item, target):
        """
        Performs the action of using an item.

        Args:
            user (obj): Character using the item
            item (obj): Item being used
            target (obj): Target of the item use
        """
        # If item is self only and no target given, set target to self.
        if item.db.item_selfonly and target is None:
            target = user

        # If item is self only, abort use if used on others.
        if item.db.item_selfonly and user != target:
            user.msg("%s can only be used on yourself." % item)
            return

        if item.db.item_notself:
            if target is user or target is None:
                user.msg(
                    f"{item.get_display_name()} can't be used on yourself. {appearance.cmd}(use <item> = <target>)")
                return

        # Set kwargs to pass to item_func
        kwargs = {}
        if item.db.kwargs:
            kwargs = item.db.kwargs

        # Match item_func string to function
        try:
            item_func = ITEMFUNCS[item.db.item_func]
        except KeyError:  # If item_func string doesn't match to a function in ITEMFUNCS
            user.msg("ERROR: %s not defined in ITEMFUNCS" % item.db.item_func)
            return

        # Call the item function - abort if it returns False, indicating an error.
        # This performs the actual action of using the item.
        # Regardless of what the function returns (if anything), it's still executed.

        # This was an "if not" check, but I could not get it to return True
        item_func(item, user, target, **kwargs)

        # If we haven't returned yet, we assume the item was used successfully.
        # Spend one use if item has limited uses
        if item.db.item_uses:
            self.spend_item_use(item, user)

        # Spend an action if in combat
        if user.is_in_combat():
            user.db.combat_turnhandler.spend_action(user, 1, action_name="item")


COMBAT = CombatHandler()

