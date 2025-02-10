from random import randint

from evennia.prototypes.spawner import spawn

from server import appearance



class BasicCombatRules:
    """
    Stores all combat rules and helper methods.

    """

    def roll_init(self, character):
        """
        Rolls a number between 1-1000 to determine initiative.

        Args:
            character (obj): The character to determine initiative for

        Returns:
            initiative (int): The character's place in initiative - higher
            numbers go first.

        Notes:
            By default, does not reference the character and simply returns
            a random integer from 1 to 1000.

            Since the character is passed to this function, you can easily reference
            a character's stats to determine an initiative roll - for example, if your
            character has a 'dexterity' attribute, you can use it to give that character
            an advantage in turn order, like so:

            return (randint(1,20)) + character.db.dexterity

            This way, characters with a higher dexterity will go first more often.
        """
        return randint(1, 20) + character.db.attribs["Dexterity"]

    def get_attack(self, attacker, defender):
        """
        Returns a value for an attack roll.

        Args:
            attacker (obj): Character doing the attacking
            defender (obj): Character being attacked

        Returns:
            attack_value (int): Attack roll value, compared against a defense value
                to determine whether an attack hits or misses.

        Notes:
            In this example, a weapon's accuracy bonus is factored into the attack
            roll. Lighter weapons are more accurate but less damaging, and heavier
            weapons are less accurate but deal more damage. Of course, you can
            change this paradigm completely in your own game.
        """
        # Start with a roll from 1 to 100.
        attack_value = randint(1, 100)
        accuracy_bonus = 0
        # If armed, add weapon's accuracy bonus.
        if attacker.db.wielded_weapon:
            weapon = attacker.db.wielded_weapon
            accuracy_bonus += weapon.db.accuracy_bonus
        # If unarmed, use character's unarmed accuracy bonus.
        """else:
            accuracy_bonus += attacker.db.unarmed_accuracy
        # Add the accuracy bonus to the attack roll."""
        attack_value += accuracy_bonus

        # Add to the roll if the attacker has the "Accuracy Up" condition.
        if "Accuracy Up" in attacker.db.conditions:  # TODO: Rename conditions to effects?
            attack_value += ACC_UP_MOD
        # Subtract from the roll if the attack has the "Accuracy Down" condition.
        if "Accuracy Down" in attacker.db.conditions:
            attack_value += ACC_DOWN_MOD

        return attack_value

    def get_defense(self, attacker, defender):
        """
        Returns a value for defense, which an attack roll must equal or exceed in order
        for an attack to hit.

        Args:
            attacker (obj): Character doing the attacking
            defender (obj): Character being attacked

        Returns:
            defense_value (int): Defense value, compared against an attack roll
                to determine whether an attack hits or misses.

        Notes:
            Characters are given a default defense value of 50 which can be
            modified up or down by armor. In this example, wearing armor actually
            makes you a little easier to hit, but reduces incoming damage.
        """
        # Start with a defense value of 50 for a 50/50 chance to hit.
        defense_value = 50
        # Modify this value based on defender's armor.
        if defender.db.worn_armor:
            armor = defender.db.worn_armor
            defense_value += armor.db.defense_modifier
        return defense_value

    def get_damage(self, attacker, defender):
        """
        Returns a value for damage to be deducted from the defender's HP after abilities
        successful hit.

        Args:
            attacker (obj): Character doing the attacking
            defender (obj): Character being damaged

        Returns:
            damage_value (int): Damage value, which is to be deducted from the defending
                character's HP.

        Notes:
            Damage is determined by the attacker's wielded weapon, or the attacker's
            unarmed damage range if no weapon is wielded. Incoming damage is reduced
            by the defender's armor.
        """
        damage_value = 0
        # Generate a damage value from wielded weapon if armed
        if attacker.db.wielded_weapon:
            weapon = attacker.db.wielded_weapon
            # Roll between minimum and maximum damage
            damage_value = randint(weapon.db.damage_range[0], weapon.db.damage_range[1])
        # Use attacker's unarmed damage otherwise
        else:
            damage_value = randint(
                attacker.db.unarmed_damage_range[0], attacker.db.unarmed_damage_range[1]
            )

        # Add to damage roll if attacker has the "Damage Up" condition.
        if "Damage Up" in attacker.db.conditions:
            damage_value += DMG_UP_MOD
            # Subtract from the roll if the attacker has the "Damage Down" condition.
        if "Damage Down" in attacker.db.conditions:
            damage_value += DMG_DOWN_MOD

        # If defender is armored, reduce incoming damage
        if defender.db.worn_armor:
            armor = defender.db.worn_armor
            damage_value -= armor.db.damage_reduction
        # Make sure minimum damage is 0
        if damage_value < 0:
            damage_value = 0
        return damage_value

    def apply_damage(self, defender, damage):
        """
        Applies damage to a target, reducing their HP by the damage amount to a
        minimum of 0.

        Args:
            defender (obj): Character taking damage
            damage (int): Amount of damage being taken
        """
        defender.db.hp -= damage  # Reduce defender's HP by the damage dealt.
        # If this reduces it to 0 or less, set HP to 0.
        if defender.db.hp <= 0:
            defender.db.hp = 0

    def at_defeat(self, defeated):
        """
        Announces the defeat of a fighter in combat.

        Args:
            defeated (obj): Fighter that's been defeated.

        Notes:
            All this does is announce a defeat message by default, but if you
            want anything else to happen to defeated fighters (like putting them
            into a dying state or something similar) then this is the place to
            do it.
        """
        defeated.location.msg_contents(f"%s{appearance.attention} has been defeated!" % defeated.get_display_name())

    def resolve_attack(
            self,
            attacker,
            defender,
            attack_value=None,
            defense_value=None,
            damage_value=None,
            inflict_condition=[],
    ):
        """
               Resolves an attack and outputs the result.

               Args:
                   attacker (obj): Character doing the attacking
                   defender (obj): Character being attacked

               Options:
                   attack_value (int): Override for attack roll
                   defense_value (int): Override for defense value
                   damage_value (int): Override for damage value
                   inflict_condition (list): Conditions to inflict upon hit, a
                       list of tuples formated as (condition(str), duration(int))

               Notes:
                   This function is called by normal attacks as well as attacks
                   made with items.
               """
        # Get the attacker's weapon type to reference in combat messages.
        attackers_weapon = "attack"
        if attacker.db.wielded_weapon:
            weapon = attacker.db.wielded_weapon
            attackers_weapon = weapon.db.weapon_type_name
        # Get an attack roll from the attacker.
        if not attack_value:
            attack_value = self.get_attack(attacker, defender)
        # Get a defense value from the defender.
        if not defense_value:
            defense_value = self.get_defense(attacker, defender)
        # If the attack value is lower than the defense value, miss. Otherwise, hit.
        if attack_value < defense_value:
            attacker.location.msg_contents(
                "%s's %s misses %s!" % (attacker.get_display_name(), attackers_weapon, defender)
            )
        else:
            damage_value = self.get_damage(attacker, defender)  # Calculate damage value.
            # Announce damage dealt and apply damage.
            if damage_value > 0:
                attacker.location.msg_contents(
                    "%s's %s strikes %s for %i damage!"
                    % (attacker, attackers_weapon, defender, damage_value)
                )
            else:
                attacker.location.msg_contents(
                    "%s's %s bounces harmlessly off %s!" % (attacker, attackers_weapon, defender)
                )
            self.apply_damage(defender, damage_value)
            # Inflict conditions on hit, if any specified
            for condition in inflict_condition:
                self.add_condition(defender, attacker, condition[0], condition[1])
            # If defender HP is reduced to 0 or less, call at_defeat.
            if defender.db.hp <= 0:
                self.at_defeat(defender)

    def combat_cleanup(self, character):
        """
        Cleans up all the temporary combat-related attributes on a character.

        Args:
            character (obj): Character to have their combat attributes removed

        Notes:
            Any attribute whose key begins with 'combat_' is temporary and no
            longer needed once a fight ends.
        """
        for attr in character.attributes.all():
            if attr.key[:7] == "combat_":  # If the attribute name starts with 'combat_'...
                character.attributes.remove(key=attr.key)  # ...then delete it!

    def is_in_combat(self, character):
        """
        Returns true if the given character is in combat.

        Args:
            character (obj): Character to determine if is in combat or not

        Returns:
            (bool): True if in combat or False if not in combat
        """
        return bool(character.db.combat_turnhandler)

    def is_turn(self, character):
        """
        Returns true if it's currently the given character's turn in combat.

        Args:
            character (obj): Character to determine if it is their turn or not

        Returns:
            (bool): True if it is their turn or False otherwise
        """
        turnhandler = character.db.combat_turnhandler
        currentchar = turnhandler.db.fighters[turnhandler.db.turn]
        return bool(character == currentchar)

    def spend_action(self, character, actions, action_name=None):
        """
        Spends a character's available combat actions and checks for end of turn.

        Args:
            character (obj): Character spending the action
            actions (int) or 'all': Number of actions to spend, or 'all' to spend all actions

        Keyword Args:
            action_name (str or None): If a string is given, sets character's last action in
            combat to provided string
        """
        if action_name:
            character.db.combat_lastaction = action_name
        if actions == "all":  # If spending all actions
            character.db.combat_actionsleft = 0  # Set actions to 0
        else:
            character.db.combat_actionsleft -= actions  # Use up actions.
            if character.db.combat_actionsleft < 0:
                character.db.combat_actionsleft = 0  # Can't have fewer than 0 actions
        character.db.combat_turnhandler.turn_end_check(character)  # Signal potential end of turn.

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
            if not item.db.item_consumable:  # Item isn't consumable
                # Just inform the player that the uses are gone
                user.msg("%s has no uses remaining." % item.key.capitalize())

            else:  # If item is consumable
                # If the value is 'True', just destroy the item
                if item.db.item_consumable:
                    user.msg("%s has been consumed." % item.key.capitalize())
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

        # Set kwargs to pass to item_func
        kwargs = {}
        if item.db.item_kwargs:
            kwargs = item.db.item_kwargs

        # Match item_func string to function
        try:
            from turnbattle.effects import ITEMFUNCS
            item_func = ITEMFUNCS[item.db.item_func]
        except KeyError:  # If item_func string doesn't match to a function in ITEMFUNCS
            user.msg("ERROR: %s not defined in ITEMFUNCS" % item.db.item_func)
            return

        # Call the item function - abort if it returns False, indicating an error.
        # This performs the actual action of using the item.
        # Regardless of what the function returns (if anything), it's still executed.
        if not item_func(item, user, target, **kwargs):
            return

        # If we haven't returned yet, we assume the item was used successfully.
        # Spend one use if item has limited uses
        if item.db.item_uses:
            self.spend_item_use(item, user)

        # Spend an action if in combat
        if self.is_in_combat(user):
            self.spend_action(user, 1, action_name="item")

    def condition_tickdown(self, character, turnchar):
        """
        Ticks down the duration of conditions on a character at the start of a given character's
        turn.

        Args:
            character (obj): Character to tick down the conditions of
            turnchar (obj): Character whose turn it currently is

        Notes:
            In combat, this is called on every fighter at the start of every character's turn. Out
            of combat, it's instead called when a character's at_update() hook is called, which is
            every 30 seconds by default.
        """

        for key in character.db.conditions:
            # The first value is the remaining turns - the second value is whose turn to count down
            # on.
            condition_duration = character.db.conditions[key][0]
            condition_turnchar = character.db.conditions[key][1]
            # If the duration is 'True', then the condition doesn't tick down - it lasts
            # indefinitely.
            if condition_duration is not True:
                # Count down if the given turn character matches the condition's turn character.
                if condition_turnchar == turnchar:
                    character.db.conditions[key][0] -= 1
                if character.db.conditions[key][0] <= 0:
                    # If the duration is brought down to 0, remove the condition and inform
                    # everyone.
                    character.location.msg_contents(
                        "%s no longer has the '%s' condition." % (str(character), str(key))
                    )
                    del character.db.conditions[key]

    def add_condition(self, character, turnchar, condition, duration):
        """
        Adds a condition to a fighter.

        Args:
            character (obj): Character to give the condition to
            turnchar (obj): Character whose turn to tick down the condition on in combat
            condition (str): Name of the condition
            duration (int or True): Number of turns the condition lasts, or True for indefinite
        """
        # The first value is the remaining turns - the second value is whose turn to count down on.
        character.db.conditions.update({condition: [duration, turnchar]})
        # Tell everyone!
        character.location.msg_contents("%s gains the '%s' condition." % (character, condition))

    # ----------------------------------------------------------------------------
    # ITEM FUNCTIONS START HERE
    # ----------------------------------------------------------------------------

    # These functions carry out the action of using an item - every item should
    # contain a db entry "item_func", with its value being a string that is
    # matched to one of these functions in the ITEMFUNCS dictionary below.

    # Every item function must take the following arguments:
    #     item (obj): The item being used
    #     user (obj): The character using the item
    #     target (obj): The target of the item use

    # Item functions must also accept **kwargs - these keyword arguments can be
    # used to define how different items that use the same function can have
    # different effects (for example, different attack items doing different
    # amounts of damage).

    # Each function below contains a description of what kwargs the function will
    # take and the effect they have on the result.

    def itemfunc_heal(self, item, user, target, **kwargs):
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

        if target.db.hp >= target.db.max_hp:
            user.msg("%s is already at full health." % target)
            return False

        min_healing = 20
        max_healing = 40

        # Retrieve healing range from kwargs, if present
        if "healing_range" in kwargs:
            min_healing = kwargs["healing_range"][0]
            max_healing = kwargs["healing_range"][1]

        to_heal = randint(min_healing, max_healing)  # Restore 20 to 40 hp
        if target.db.hp + to_heal > target.db.max_hp:
            to_heal = target.db.max_hp - target.db.hp  # Cap healing to max HP
        target.db.hp += to_heal

        user.location.msg_contents("%s uses %s! %s regains %i HP!" % (user, item, target, to_heal))

    def itemfunc_add_condition(self, item, user, target, **kwargs):
        """
        Item function that gives the target one or more conditions.

        kwargs:
            conditions (list): Conditions added by the item
               formatted as a list of tuples: (condition (str), duration (int or True))

        Notes:
            Should mostly be used for beneficial conditions - use itemfunc_attack
            for an item that can give an enemy a harmful condition.
        """
        conditions = [("Regeneration", 5)]

        if not target:
            target = user  # Target user if none specified

        if not target.attributes.has("max_hp"):  # Is not a fighter
            user.msg("You can't use %s on that." % item)
            return False  # Returning false aborts the item use

        # Retrieve condition / duration from kwargs, if present
        if "conditions" in kwargs:
            conditions = kwargs["conditions"]

        user.location.msg_contents("%s uses %s!" % (user, item))

        # Add conditions to the target
        for condition in conditions:
            self.add_condition(target, user, condition[0], condition[1])

    def itemfunc_cure_condition(self, item, user, target, **kwargs):
        """
        Item function that'll remove given conditions from a target.

        kwargs:
            to_cure(list): List of conditions (str) that the item cures when used
        """
        to_cure = ["Poisoned"]

        if not target:
            target = user  # Target user if none specified

        if not target.attributes.has("max_hp"):  # Is not a fighter
            user.msg("You can't use %s on that." % item)
            return False  # Returning false aborts the item use

        # Retrieve condition(s) to cure from kwargs, if present
        if "to_cure" in kwargs:
            to_cure = kwargs["to_cure"]

        item_msg = "%s uses %s! " % (user, item)

        for key in target.db.conditions:
            if key in to_cure:
                # If condition specified in to_cure, remove it.
                item_msg += "%s no longer has the '%s' condition. " % (str(target), str(key))
                del target.db.conditions[key]

        user.location.msg_contents(item_msg)

    def itemfunc_attack(self, item, user, target, **kwargs):
        """
        Item function that attacks a target.

        kwargs:
            min_damage(int): Minimum damage dealt by the attack
            max_damage(int): Maximum damage dealth by the attack
            accuracy(int): Bonus / penalty to attack accuracy roll
            inflict_condition(list): List of conditions inflicted on hit,
                formatted as a (str, int) tuple containing condition name
                and duration.

        Notes:
            Calls resolve_attack at the end.
        """
        if not self.is_in_combat(user):
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

        min_damage = 20
        max_damage = 40
        accuracy = 0
        inflict_condition = []

        # Retrieve values from kwargs, if present
        if "damage_range" in kwargs:
            min_damage = kwargs["damage_range"][0]
            max_damage = kwargs["damage_range"][1]
        if "accuracy" in kwargs:
            accuracy = kwargs["accuracy"]
        if "inflict_condition" in kwargs:
            inflict_condition = kwargs["inflict_condition"]

        # Roll attack and damage
        attack_value = randint(1, 100) + accuracy
        damage_value = randint(min_damage, max_damage)

        # Account for "Accuracy Up" and "Accuracy Down" conditions
        if "Accuracy Up" in user.db.conditions:
            attack_value += 25
        if "Accuracy Down" in user.db.conditions:
            attack_value -= 25

        user.location.msg_contents("%s attacks %s with %s!" % (user, target, item))
        self.resolve_attack(
            user,
            target,
            attack_value=attack_value,
            damage_value=damage_value,
            inflict_condition=inflict_condition,
        )


TURN_TIMEOUT = 30  # Time before turns automatically end, in seconds
ACTIONS_PER_TURN = 1  # Number of actions allowed per turn
NONCOMBAT_TURN_TIME = 30  # Time per turn count out of combat
REGEN_RATE = (4, 8)  # Min and max HP regen for Regeneration
POISON_RATE = (4, 8)  # Min and max damage for Poisoned
ACC_UP_MOD = 25  # Accuracy Up attack roll bonus
ACC_DOWN_MOD = -25  # Accuracy Down attack roll penalty
DMG_UP_MOD = 5  # Damage Up damage roll bonus
DMG_DOWN_MOD = -5  # Damage Down damage roll penalty
DEF_UP_MOD = 15  # Defense Up defense bonus
DEF_DOWN_MOD = -15  # Defense Down defense penalty
COMBAT_RULES = BasicCombatRules()
