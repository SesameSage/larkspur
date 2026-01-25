from random import randint

from evennia.prototypes.spawner import spawn

from combat.combat_constants import PERCEPT_TO_ACCURACY_BONUS
from server import appearance
from server.appearance import dmg_color
from combat.effects import DamageTypes
from typeclasses.inanimate.items.equipment.weapons import Weapon
from typeclasses.inanimate.items.items import ITEMFUNCS
from typeclasses.inanimate.items.usables import Consumable


class CombatHandler:
    """
    Handles many combat interactions and calculations as a single instance per server load.
    Functions in this file are listed in the order of their step-by-step logic.
    """

    def get_ap(self, character):
        """
        Returns the amount of AP a character gains this turn based on their stats.

        :param character: Character generating AP.
        :return: Amount of AP gained this turn.
        """
        DEX_BONUS = character.get_attr("dex") // 2
        ap = 2
        ap += DEX_BONUS
        character.location.more_info(f"{DEX_BONUS} AP from Dexterity")
        for effect in ("+AP", "-AP"):
            if character.effect_active(effect):
                effect_amt = character.db.effects[effect]["amount"]
                source = character.db.effects[effect]["source"].key
                ap += effect_amt
                character.location.more_info(f"{effect_amt} AP from {source}")

        return ap

    def get_allies(self, character):
        allies = []
        if character.is_in_combat():
            container = character.db.combat_turnhandler.db.fighters
        else:
            container = character.location.contents

        for content in container:
            if content.db.hostile_to_players == character.db.hostile_to_players:
                allies.append(content)
        return allies

    def get_enemies(self, character):
        enemies = []
        if character.is_in_combat():
            container = character.db.combat_turnhandler.db.fighters
        else:
            container = character.location.contents

        for content in container:
            if (content.attributes.has("hostile_to_players")
                    and content.db.hostile_to_players != character.db.hostile_to_players):
                enemies.append(content)
        return enemies

    def action_range(self, action):
        return 1 if isinstance(action, str) else action.db.range

    def check_range(self, attacker, target, action):
        rng = self.action_range(action)
        if not rng or rng == 0:
            return True
        if attacker.is_in_combat() and attacker.db.combat_turnhandler.db.grid.distance(attacker, target) > rng:
            attacker.msg("Out of range!")
            return False
        else:
            return True

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
        accuracy = hitroll
        attacker.location.more_info(f"Hitroll {hitroll} ({attacker.name})")
        accuracy_bonus = 0
        # If armed, add weapon's accuracy bonus.
        weapon = attacker.get_weapon()
        if not isinstance(weapon, str):
            accuracy_bonus += weapon.db.accuracy_buff
            attacker.location.more_info(f"+{accuracy_bonus} accuracy from {weapon.name} ({attacker.name})")
        accuracy += accuracy_bonus

        # Add Perception bonus
        amt = PERCEPT_TO_ACCURACY_BONUS[attacker.get_attr("perception")]
        accuracy += amt
        attacker.location.more_info(f"{amt} accuracy from perception ({attacker.name})")

        # Apply attacker's hitroll buffs and debuffs.
        if "+Accuracy" in attacker.db.effects:
            buff = attacker.db.effects["+Accuracy"]["amount"]
            accuracy += buff
            attacker.location.more_info(f"{buff} accuracy from effect on {attacker.name}")
        if "-Accuracy" in attacker.db.effects:
            buff = attacker.db.effects["-Accuracy"]["amount"]
            accuracy += buff
            attacker.location.more_info(f"{buff} accuracy from effect on {attacker.name}")

        if "Blinded" in attacker.db.effects:
            accuracy = (accuracy) // 2
            attacker.location.more_info("-50% accuracy from Blinded")

        attacker.location.more_info(f"{accuracy} to hit ({attacker.name})")
        return accuracy

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
        attacker.location.more_info(f"Accuracy {accuracy}, Evasion {evasion_value}")
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
        attacker.location.more_info(
            str([f"{damage_type.get_display_name() if damage_type else "Physical Damage"}: {damage_values[damage_type]}"
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
        for damage_type in DamageTypes:
            effect_amt = 0
            effect_keys = [f"+{damage_type.get_display_name(capital=True)} Dmg",
                           f"-{damage_type.get_display_name(capital=True)} Dmg",
                           f"+Damage", f"-Damage"] if damage_type else [f"+Damage", f"-Damage"]

            for effect_key in effect_keys:
                if effect_key in attacker.db.effects:
                    effect_amt += attacker.db.effects[effect_key]["amount"]
            if effect_amt != 0:
                attacker.location.more_info(
                    f"{effect_amt}{" " + damage_type.get_display_name() if damage_type else ""} "
                    f"damage from effect on {attacker.name}")
                try:
                    damage_values[damage_type] += effect_amt
                except KeyError:
                    damage_values[damage_type] = effect_amt

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
            damage = damage_values[damage_type]
            type_name = " " + damage_type.get_display_name() if damage_type else ""

            defender.location.more_info(f"{damage}{type_name} damage coming "
                                        f"at {defender.name}")

            # Get defense for physical damage
            if damage_type in [DamageTypes.BLUNT, DamageTypes.SLASHING, DamageTypes.PIERCING]:
                defense = defender.get_defense(damage_type)
                damage -= defense
                if defense > 0:
                    defender.location.more_info(f"-{defense}{type_name} damage from defense")

            # Get resistance for magical/other damage
            elif damage_type in [DamageTypes.FIRE, DamageTypes.COLD, DamageTypes.SHOCK, DamageTypes.POISON]:
                resistance = defender.get_resistance(damage_type)
                damage -= resistance
                if resistance > 0:
                    defender.location.more_info(
                        f"-{resistance}{type_name} damage from resistance")

            # Make sure minimum damage is 0
            if damage < 0:
                damage = 0

            # Adjust damage values dict
            damage_values[damage_type] = damage
            defender.location.more_info(f"{damage} final{type_name} damage")

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
                type_name = " " + damage_type.get_display_name() if damage_type else ""
                msg = msg + f"{dmg_color(attacker)}{damage_values[damage_type]}{type_name}|n"
            # End with " damage!"
            msg = msg + f"{dmg_color(attacker)} damage!|n"
            attacker.location.msg_contents(msg)

        else:  # No damage dealt
            attacker.location.msg_contents(
                "%s's %s bounces harmlessly off %s!" % (
                    attacker.get_display_name(article=True, capital=True), attack_name,
                    defender.get_display_name(article=True))
            )

    def resolve_attack(
            self,
            attacker,
            defender,
            attack,
            accuracy=None,
            evasion=None,
            damage_values=None,
            announce_msg=None,
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
        def get_damage_values(damage_values):
            if not damage_values:
                # If attacking with weapon or unarmed
                if isinstance(attack, Weapon) or isinstance(attack, str):
                    damage_values = self.get_weapon_damage(attacker)
                # Else attacking with ability
                else:
                    damage_values = attack.get_damage(attacker)

            damage_values = self.apply_damage_amt_effects(attacker, defender, damage_values)
            damage_values = self.get_damage_taken(defender, damage_values)
            damage_values = {key: value for key, value in damage_values.items() if value > 0}
            total_damage = 0
            for damage_type in damage_values:
                total_damage += damage_values[damage_type]

            return damage_values, total_damage

        def apply_post_attack_effects():
            if (defender.attributes.has("rpg_class") and defender.db.rpg_class
                    and defender.db.rpg_class.__name__ == "Monk" and defender.db.combat_lastaction == "pass"):
                attacker.location.msg_contents(f"{defender.get_display_name(capital=True)} counterattacks!")
                defender.attack(attacker)
            if defender.effect_active("Retaliation"):
                effect = defender.db.effects["Retaliation"]
                retal_damage = self.get_damage_taken(attacker, {effect["damage_type"]: effect["amount"]})
                attacker.apply_damage(retal_damage)
                defender.location.msg_contents(f"{attacker.get_display_name(capital=True)} takes "
                                               f"{retal_damage[effect["damage_type"]]} damage from "
                                               f"{defender.get_display_name()}'s {appearance.effect}Retaliation|n!")
            if attacker.effect_active("Cursed"):
                amount = attacker.db.effects["Cursed"]["amount"]
                attacker.apply_damage({DamageTypes.ARCANE: amount})
                attacker.location.msg_contents(f"{attacker.get_display_name(capital=True)} takes {amount} damage from "
                                               f"their curse!")
            if attacker.effect_active("Siphon HP"):
                siphoned = int(total_damage / 3)
                attacker.db.hp += siphoned
                attacker.location.msg_contents(f"{attacker.get_display_name(capital=True)} siphons {siphoned} HP from "
                                               f"{defender.get_display_name()}!")
                attacker.cap_stats()
            if attacker.effect_active("Siphon Mana"):
                siphoned = int(total_damage / 2)
                attacker.db.mana += siphoned
                attacker.location.msg_contents(
                    f"{attacker.get_display_name(capital=True)} siphons {siphoned} mana from "
                    f"{defender.get_display_name()}!")
                attacker.cap_stats()
            if attacker.effect_active("Siphon Stamina"):
                siphoned = int(total_damage / 2)
                if attacker.db.stamina < siphoned:
                    if attacker.db.stamina == 0:
                        attacker.location.msg_contents(
                            f"{defender.get_display_name(capital=True)} doesn't have enough stamina to siphon!")
                    else:
                        siphoned = defender.db.stamina
                        defender.db.stamina = 0
                        attacker.db.stamina += siphoned
                else:
                    defender.db.stamina -= siphoned
                    attacker.db.stamina += siphoned
                attacker.location.msg_contents(
                    f"{attacker.get_display_name(capital=True)} siphons {siphoned} stamina from "
                    f"{defender.get_display_name()}!")
                attacker.cap_stats()
                defender.cap_stats()

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
                "%s's %s misses %s!" % (
                    attacker.get_display_name(capital=True), attack_name, defender.get_display_name(article=True))
            )
            return attack_landed, {}

        # Get damage
        damage_values, total_damage = get_damage_values(damage_values)

        # Announce and apply damage
        self.announce_damage(attacker=attacker, defender=defender, attack_name=attack_name, damage_values=damage_values,
                             msg=announce_msg)
        if bool(damage_values):
            defender.apply_damage(damage_values)

        # Apply post-attack effects
        apply_post_attack_effects()

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
