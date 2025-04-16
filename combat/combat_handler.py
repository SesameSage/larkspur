from random import randint

from evennia.prototypes.spawner import spawn

from server import appearance
from server.appearance import dmg_color
from combat.effects import DamageTypes
from typeclasses.inanimate.items.equipment.weapons import Weapon
from typeclasses.inanimate.items.items import ITEMFUNCS
from typeclasses.inanimate.items.usables import Consumable

HITROLL_PERCEPTION_BONUS = 2


class CombatHandler:

    def get_accuracy(self, attacker, defender):
        """
        Returns an accuracy for an attack, applying only the attacker's stat modifications to a hitroll.

        Args:
            attacker (obj): Character doing the attacking
            defender (obj): Character being attacked

        Returns:
            hitroll (int): Accuracy value to be compared against a defense value
                to determine whether an attack hits or misses.
        """
        # Start with a roll from 1 to 100.
        hitroll = randint(1, 100)
        attacker.location.more_info(f"Hitroll {hitroll} ({attacker.name})")
        accuracy_bonus = 0
        # If armed, add weapon's accuracy bonus.
        weapon = attacker.get_weapon()
        if not isinstance(weapon, str):
            accuracy_bonus += weapon.db.accuracy_bonus
            attacker.location.more_info(f"+{accuracy_bonus} accuracy from {weapon.name} ({attacker.name})")
        hitroll += accuracy_bonus

        # Add Perception bonus
        hitroll += attacker.get_attr("perception") * HITROLL_PERCEPTION_BONUS

        # Apply attacker's hitroll buffs and debuffs.
        buff = 0
        if "Accuracy Up" in attacker.db.effects:
            buff += attacker.db.effects["Accuracy Up"]["amount"]
        if "Blinded" in attacker.db.effects:
            buff -= (hitroll) // 2
            attacker.location.more_info("-50% accuracy from Blinded")
        hitroll += buff

        attacker.location.more_info(f"{hitroll} to hit ({attacker.name})")
        return hitroll

    def hit_successful(self, attacker=None, defender=None, accuracy=None, evasion_value=None):
        """
        Determines whether an attack successfully lands. Either attacker/defender or accuracy/evasion must be provided.

        Args:
            attacker (CombatEntity): The entity attacking.
            defender (CombatEntity): The entity being attacked.
            accuracy (int): A hitroll value for the attack, or chance of landing.
            evasion_value: The total get_evasion value of the defender.

        Returns:
            Boolean whether the hit was successful.
        """
        # Get an attack roll from the attacker.
        if not accuracy:
            if attacker is None or defender is None:
                return None
            accuracy = self.get_accuracy(attacker, defender)
        # Get an evasion value from the defender.
        if not evasion_value:
            evasion_value = defender.get_evasion()

        # If the attack value is lower than the defense value, miss. Otherwise, hit.
        if accuracy < evasion_value:
            attacker.location.more_info(f"{accuracy} hit < {evasion_value} evasion (miss)")
            return False
        else:
            attacker.location.more_info(f"{accuracy} hit > {evasion_value} evasion (success)")
            return True

    def get_weapon_damage(self, attacker):
        """
        Rolls for wielded weapon or unarmed damage.

        Args:
            attacker (CombatEntity): Entity attacking

        Returns:
            damage_values (dict): Damage types and values to adjust for effects and pass to the defender's def/resist.
        """
        damage_values = {}
        # Generate a damage value from wielded weapon if armed
        weapon = attacker.get_weapon()
        if not isinstance(weapon, str):
            for damage_type in weapon.db.damage_ranges:
                # Roll between minimum and maximum damage
                range = weapon.db.damage_ranges[damage_type]
                damage_values[damage_type] = randint(range[0], range[1])
                attacker.location.more_info(
                    f"+{damage_values[damage_type]} {damage_type.get_display_name()} damage from {weapon.name} ({attacker.name})")
                # Make sure minimum damage is 0
                if damage_values[damage_type] < 0:
                    damage_values[damage_type] = 0

        # If not armed, use unarmed damage
        else:
            for damage_type in attacker.db.unarmed_damage:
                range = attacker.db.unarmed_damage[damage_type]
                damage_values[damage_type] = randint(range[0], range[1])

        attacker.location.more_info(f"Damage roll ({attacker.name}):")
        attacker.location.more_info(str([f"{damage_type.get_display_name() if damage_type else "Physical Damage"}: {damage_values[damage_type]}"
                                         for damage_type in damage_values]))

        return damage_values

    def apply_damage_amt_effects(self, attacker, defender, damage_values):
        """
        Applies to the given damage_values any effects on the attacker or defender that increase or decrease damage.

        Args:
            attacker (CombatEntity): Entity attacking
            defender (CombatEntity): Entity being attacked
            damage_values: The damage values calculated from the hit, to be passed to the defender's defense / resist.

        Returns:
            Adjusted damage values to pass to the defender's get_damage_taken method.
        """
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
        if defender.effect_active("Knocked Down"):  # If defender knocked down, add 50% to damage
            defender.location.more_info("+50% damage (Knocked Down)")
            for damage_type in damage_values:
                damage_values[damage_type] += damage_values[damage_type] // 2

        return damage_values

    def get_damage_taken(self, defender, damage_values):
        """
        Apply defense and resistance to determine the damage that is actually taken by the defender.

        Args:
            defender: The entity taking the hit.
            damage_values: The damage_values calculated for the attack, already including attacker and defender's effects.

        Returns:
            The damage values to actually deduct from the defender's HP
        """
        # For each type of damage being dealt
        for damage_type in damage_values:

            # Get defense for physical damage
            if damage_type in [DamageTypes.BLUNT, DamageTypes.SLASHING, DamageTypes.PIERCING]:
                defense = defender.get_defense(damage_type)
                damage_values[damage_type] -= defense
                if defense > 0:
                    defender.location.more_info(f"-{defense} {damage_type.get_display_name()} damage from defense")

            # Get resistance for magical/other damage
            elif damage_type in [DamageTypes.FIRE, DamageTypes.COLD, DamageTypes.SHOCK, DamageTypes.POISON]:
                resistance = defender.get_resistance(damage_type)
                damage_values[damage_type] -= resistance
                if resistance > 0:
                    defender.location.more_info(f"-{resistance} {damage_type.get_display_name()} damage from resistance")

            # Make sure minimum damage is 0
            if damage_values[damage_type] < 0:
                damage_values[damage_type] = 0

        return damage_values

    def announce_damage(self, attacker, defender, damage_values, attack_name=None, msg=None):
        """
        Announce the strike or miss of an attack, and the damages dealt on a strike, to everyone in the room.

        Args:
            attacker (CombatEntity): Entity attacking.
            defender (CombatEntity): Entity being attacked.
            damage_values: The damage that was actually taken by the defender.
            attack_name: The weapon object, ability/spell object, or string name of the unarmed attack being used.
            msg: Optional replacement message up to "x damage!" that different abilities can specify
        """
        if bool(damage_values):  # If any damages are > 0
            # Craft grammatically accurate one-line list of damages i.e. "5 blunt, 3 piercing, and 2 fire damage!"
            if not msg:
                msg = "%s's %s strikes %s for " % (
                    attacker.get_display_name(capital=True), attack_name, defender.get_display_name(article=True))
            for i, damage_type in enumerate(damage_values):
                if i == len(damage_values) - 1 and len(damage_values) > 1:  # If at the last damage type to list
                    # Precede with " and "
                    if msg[-1] != " ":
                        msg = msg + " "
                    msg = msg + "and "
                elif len(damage_values) > 2:  # Else if there are more to list
                    # Follow with a comma
                    msg = msg + ", "
                # Add damage amount and type to message
                msg = msg + f"{dmg_color(attacker, defender)}{damage_values[damage_type]} {damage_type.get_display_name()}|n"
            # End with " damage!"
            msg = msg + f"{dmg_color(attacker, defender)} damage!|n"
            attacker.location.msg_contents(msg)

        else:  # No damage dealt
            attacker.location.msg_contents(
                "%s's %s bounces harmlessly off %s!" % (
                    attacker.get_display_name(article=True, capital=True), attack_name, defender.get_display_name(article=True))
            )

    def resolve_attack(
            self,
            attacker,
            defender,
            attack,
            accuracy=None,
            evasion=None,
            damage_values=None,
            announce_msg = None,
            inflict_condition=[],
    ):
        """
               Checks if an attack hits or misses, calculates the damage, and applies it, along with announcements.

               Args:
                   attacker (CombatEntity): Entity attacking
                   defender (CombatEntity): Entity being attacked
                   attack: The weapon object, ability/spell object, or name of unarmed attack being used

               Options:
                   accuracy (int): Override for hitroll. Default will run attacker.get_accuracy
                   evasion (int): Override for evasion. Default will run defender.get_evasion
                   damage_values (dict): Override for damage values. Default will use weapon.get_weapon_damage or
                        ability.get_damage
                   inflict_condition (list): Conditions to inflict upon hit, a list of tuples
                        formatted as (condition(str), duration(int))

                Returns (bool, dict):
                    Tuple of boolean whether the hit landed, and the final damage values taken by the defender.
               """
        # Extract attack name
        if isinstance(attack, str):
            attack_name = attack
        else:
            attack_name = attack.get_display_name()

        # Check if hit or miss
        attack_landed = True
        if not self.hit_successful(attacker, defender, accuracy, evasion):
            attack_landed = False
            attacker.location.msg_contents(
                "%s's %s misses %s!" % (attacker.get_display_name(capital=True), attack_name, defender.get_display_name(article=True))
            )
            return attack_landed, {}

        if not damage_values:
            # If attacking with weapon or unarmed
            if isinstance(attack, Weapon) or isinstance(attack, str):
                damage_values = self.get_weapon_damage(attacker)
            else:  # Attacking with ability
                damage_values = attack.get_damage(attacker)

        damage_values = self.apply_damage_amt_effects(attacker, defender, damage_values)
        damage_values = self.get_damage_taken(defender, damage_values)
        damage_values = {key: value for key, value in damage_values.items() if value > 0}

        # Announce and apply damage
        self.announce_damage(attacker=attacker, defender=defender, attack_name=attack_name, damage_values=damage_values, msg=announce_msg)
        if bool(damage_values):
            defender.apply_damage(damage_values)

        if defender.effect_active("Retaliation"):
            effect = defender.db.effects["Retaliation"]
            retal_damage = self.get_damage_taken(attacker, {effect["damage_type"]: effect["amount"]})
            attacker.apply_damage(retal_damage)
            defender.location.msg_contents(f"{attacker.get_display_name(capital=True)} takes "
                                           f"{retal_damage[effect["damage_type"]]} damage from "
                                           f"{defender.get_display_name()}'s {appearance.effect}Retaliation|n!")
        """# Inflict conditions on hit, if any specified
        for condition in inflict_condition:
            self.add_effect(defender, attacker, condition[0], condition[1])"""

        return attack_landed, damage_values

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
