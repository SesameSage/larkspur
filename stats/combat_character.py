from decimal import Decimal as Dec

import evennia
from evennia import TICKER_HANDLER as tickerhandler
from evennia.utils import inherits_from

from combat.combat_handler import COMBAT
from combat.effects import EffectScript, DurationEffect
from combat.turn_handler import start_join_fight
from server import appearance
from stats.stats_constants import MAX_HP_BASE, LVL_TO_MAXHP, CON_TO_MAXHP, MAX_MANA_BASE, LVL_TO_MAXMANA, \
    SPIRIT_TO_MAXMANA, MAX_STAM_BASE, LVL_TO_MAXSTAM, STR_TO_MAXSTAM, CON_TO_DEFENSE, DEXT_TO_EVADE, WIS_TO_RESIST
from typeclasses.inanimate.fixtures import Fireplace
from typeclasses.inanimate.items.equipment.equipment import EquipmentEntity
from typeclasses.living.corpses import make_corpse, set_to_respawn
from world.quests.quest import quest_desc


class CombatEntity(EquipmentEntity):
    """
    A character able to participate in turn-based combat. Has attributes for current
    and maximum HP, and access to combat commands.
    """

    def at_object_creation(self):
        """
        Called once, when this object is first created. This is the
        normal hook to overload for most object types.
        """
        super().at_object_creation()

        self.db.ai = None
        self.db.rpg_class = None
        self.db.level = 1
        self.db.attribs = {"strength": 1, "constitution": 1,
                           "dexterity": 1, "perception": 1, "intelligence": 1,
                           "wisdom": 1, "spirit": 1}

        self.db.max_hp = MAX_HP_BASE
        self.db.hp = self.db.max_hp
        self.db.hp_regen = round(Dec(0.2), 2)
        self.db.hp_buildup = Dec(0.0)

        self.db.max_stam = MAX_STAM_BASE
        self.db.stamina = self.db.max_stam
        self.db.stam_regen = round(Dec(0.2), 2)
        self.db.stam_buildup = Dec(0.0)

        self.db.max_mana = MAX_MANA_BASE
        self.db.mana = self.db.max_mana
        self.db.mana_regen = round(Dec(0.2), 2)
        self.db.mana_buildup = Dec(0.0)

        self.db.abilities = []

        self.db.mods = {}
        self.db.effects = {}

        self.db.cooldowns = {}

        self.db.hostile_to_players = False
        self.db.dies = True
        self.db.quest_hooks = {"at_defeat": {}}

        tickerhandler.add(1, self.at_tick, idstring="tick_effects")

        self.update_base_stats()

    # <editor-fold desc="Tick methods">
    def at_tick(self):
        """Executes every second when out of combat, allowing finer control of its effects in combat."""
        if not self.is_in_combat():
            self.apply_effects()
            self.tick_cooldowns()
            if not self.is_in_combat():
                self.regenerate()

    def tick_cooldowns(self, secs=1):
        """Increments any active cooldowns down by 1 or the given number of seconds."""
        for ability in self.db.cooldowns:
            self.db.cooldowns[ability] -= secs
            if self.db.cooldowns[ability] < 0:
                self.db.cooldowns[ability] = 0

    def regenerate(self, secs=1):
        """
        Increments hp, mana, and stamina by their per-second regen values from this entity's stats.

        These regen values may be less than 1 hp/mana/stamina per second, but the target stats work in whole numbers.
        Consequently, fractional progress toward the next point gained is stored in a buildup counter on the entity.

        For example, if a player's hp_regen is 0.25, they heal 1 hp every 4 seconds. Their hp_buildup will progress
        0 > 0.25 > 0.50 > 0.75 > 1.00. On the 4th second, upon reaching 1.00, the player's hp will increase by 1, and
        the hp_buildup will lose that 1.00, carrying any overflow fraction with it (so 1.15 becomes 0.15 buildup).

        The buildup also carries fractional overflow for regen values over 1, for example handling the additional point
        added every 4 seconds for a regen value of 2.25, while still accurately incrementing the regular 2 per second.
        """
        #Regenerate everything 3x faster in rooms with fireplaces
        if self.location and inherits_from(self.location, "world.locations.rooms.Room"):
            if self.location.in_room(Fireplace):
                secs = 3 * secs

        self.db.hp_buildup += self.get_regen("hp") * secs
        self.db.mana_buildup += self.get_regen("mana") * secs
        if not self.effect_active("Winded"):
            self.db.stam_buildup += self.get_regen("stam") * secs

        if self.db.hp_buildup >= 1:
            hp_gained = int(self.db.hp_buildup)
            self.db.hp_buildup -= Dec(hp_gained)
            self.db.hp += hp_gained
        if self.db.mana_buildup >= 1:
            mana_gained = int(self.db.mana_buildup)
            self.db.mana_buildup -= Dec(mana_gained)
            self.db.mana += mana_gained
        if self.db.stam_buildup >= 1:
            stam_gained = int(self.db.stam_buildup)
            self.db.stam_buildup -= Dec(stam_gained)
            self.db.stamina += stam_gained
        self.cap_stats()

    # </editor-fold>

    # <editor-fold desc="Stats handling">
    # <editor-fold desc="Get stats in current effective form">
    def get_attr(self, att_input: str):
        """Gets the current effective Strength, Intelligence, etc. for this entity by attribute name."""
        # Standardize to full capitalized name
        for attribute in self.db.attribs:
            if attribute.startswith(att_input):
                break

        # Base attribute tied to the character's stats
        base_attr = self.db.attribs[attribute]

        attribute = attribute.capitalize()
        # Bonus from effects
        effect = 0
        if f"+{attribute}" in self.db.effects:
            effect += self.db.effects[f"+{attribute}"]["amount"]
        if f"-{attribute}" in self.db.effects:
            effect -= self.db.effects[f"-{attribute}"]["amount"]

        return base_attr + effect

    def get_defense(self, damage_type=None, type_only=False, quiet=False):
        """Returns the current effective defense for this entity, including equipment and effects."""
        # Untyped defense
        base_def = 0
        if not type_only:
            try:
                base_def = self.db.char_defense[None]
            except KeyError:
                base_def = 0
            if not quiet:
                self.location.more_info(f"{base_def} untyped defense ({self.name})")

        # Typed defense
        dt_def = 0
        if damage_type:  # If we are getting defense from a specific damage type
            try:
                dt_def = self.db.char_defense[damage_type]
                if not quiet:
                    self.location.more_info(f"{dt_def} {damage_type.get_display_name()} resistance ({self.name})")
            except KeyError:  # Move on if we don't have defense of this type
                pass

        # Defense from equipment
        eq_defense = 0
        for slot in self.db.equipment:
            this_eq_def = 0  # Total defense from this piece of equipment, for display
            equipment = self.db.equipment[slot]
            if equipment and equipment.attributes.has("defense"):  # If equipment found with defense attr to access
                # Add equipment's untyped defense if present
                if not type_only:
                    try:
                        if equipment.db.defense[None] != 0:
                            this_eq_def += equipment.db.defense[None]
                            if not quiet:
                                self.location.more_info(f"{this_eq_def} defense from {equipment.name}")
                    except KeyError:  # Move on if it provides no untyped defense (only typed)
                        pass

                if damage_type is not None:  # If we are getting defense from a specific damage type
                    try:
                        if equipment.db.defense[damage_type] != 0:
                            this_eq_def += equipment.db.defense[damage_type]  # Add eq's defense against this type
                            if not quiet:
                                self.location.more_info(f"{equipment.db.defense[damage_type]} "
                                                        f"{damage_type.get_display_name()} "
                                                        f"defense from {equipment.name}")
                    except KeyError:  # Move on if this equipment doesn't provide defense against this damage type
                        pass
                if this_eq_def != 0:
                    eq_defense += this_eq_def  # Add this equipment piece's total defense from this damage
        # If armor is being ignored, subtract a percentage
        if self.effect_active("Armor Ignored"):
            percent = self.db.effects["Armor Ignored"]["amount"]
            decimal = Dec(percent) / Dec(100)
            armor_ignored = decimal * eq_defense
            self.location.more_info(f"{percent}% of {eq_defense} armor ignored = {armor_ignored}")
            eq_defense -= armor_ignored

        effect_def = 0
        if "+Defense" in self.db.effects:
            effect_def += self.db.effects["+Defense"]["amount"]
        if "-Defense" in self.db.effects:
            effect_def += self.db.effects["-Defense"]["amount"]
        if effect_def > 0 and not quiet:
            self.location.more_info(f"{"+" if effect_def > 0 else ""}{effect_def} defense from effects ({self.name})")

        return base_def + dt_def + eq_defense + effect_def

    def get_evasion(self, quiet=False):
        """Returns the current effective evasion for this entity, including equipment and effects."""
        # Base evasion on character
        if not quiet:
            self.location.more_info(f"{self.db.char_evasion} base evasion ({self.name})")

        # Equipment evasion bonuses
        eq_ev = 0
        weight_ev = 0
        for slot in self.db.equipment:
            equipment = self.db.equipment[slot]
            if equipment:
                if hasattr(equipment.db, "evasion") and equipment.db.evasion:
                    eq_ev += equipment.db.evasion
                    if not quiet:
                        self.location.more_info(f"+{equipment.db.evasion} evasion from {equipment.name} ({self.name})")
                weight_ev -= equipment.db.weight // 2  # May need to scale with level
                if not quiet:
                    self.location.more_info(f"{weight_ev} evasion from equipment weight")

        # Evasion bonuses from effects
        effect_ev = 0
        if "+Evasion" in self.db.effects:
            effect_ev += self.db.effects["+Evasion"]["amount"]
        if "-Evasion" in self.db.effects:
            effect_ev += self.db.effects["-Evasion"]["amount"]
        if effect_ev > 0 and not quiet:
            self.location.more_info(f"{"+" if effect_ev > 0 else ""}{effect_ev} evasion from effect ({self.name})")

        total_ev = self.db.char_evasion + weight_ev + eq_ev + effect_ev
        total_ev = 0 if total_ev < 0 else total_ev
        return total_ev

    def get_resistance(self, damage_type=None, type_only=False, quiet=False):
        """Returns the current effective resistance for this entity, including equipment and effects."""
        # Untyped resistance
        base_resist = 0
        if not type_only:
            base_resist = self.db.char_resistance[None]
            if not quiet:
                self.location.more_info(f"{base_resist} base resistance ({self.name})")

        # Typed resistance
        dt_resist = 0
        if damage_type:  # If we are getting resistance for a specific damage type
            try:
                dt_resist = self.db.char_resistance[damage_type]
                if not quiet:
                    self.location.more_info(f"{dt_resist} {damage_type.get_display_name()} resistance ({self.name})")
            except KeyError:  # Move on if we don't have resistance of this type
                pass

        # Resistance from equipment
        eq_resist = 0
        for slot in self.db.equipment:
            this_eq_res = 0  # Total defense from this piece of equipment, for display
            equipment = self.db.equipment[slot]
            if equipment and equipment.attributes.has("resistance"):  # If equipment found with resist attr to access
                # Add equipment's untyped defense if present
                if not type_only:
                    try:
                        if equipment.db.resistance[None] != 0:
                            this_eq_res += equipment.db.resistance[None]
                            if not quiet:
                                self.location.more_info(f"{this_eq_res} resistance from {equipment.name}")
                    except KeyError:  # Move on if it provides no untyped defense (only typed)
                        pass

                if damage_type is not None:  # If we are getting resistance for a specific damage type
                    try:
                        if equipment.db.resistance[damage_type] != 0:
                            this_eq_res += equipment.db.resistance[damage_type]  # Add eq's resist against this type
                            self.location.more_info(f"{equipment.db.resistance[damage_type]} "
                                                    f"{damage_type.get_display_name()} "
                                                    f"resistance from {equipment.name}")
                    except KeyError:  # Move on if this equipment doesn't provide resistance against this damage type
                        pass
                if this_eq_res != 0:
                    eq_resist += this_eq_res  # Add this equipment piece's total resistance to this damage

        effect_resist = 0
        if "+Resistance" in self.db.effects:
            amount = self.db.effects["+Resistance"]["amount"]
            effect_resist += amount
            if not quiet:
                self.location.more_info(f"{amount} resistance from effect")
        if "-Resistance" in self.db.effects:
            effect_resist += self.db.effects["-Resistance"]["amount"]
            if not quiet:
                self.location.more_info(f"{amount} resistance from effect")
        if damage_type:
            dmg_typ_name = damage_type.get_display_name(capital=True)
            if f"+{dmg_typ_name} Resist" in self.db.effects:
                amount = self.db.effects[f"+{dmg_typ_name} Resist"]["amount"]
                effect_resist += amount
                if not quiet:
                    self.location.more_info(f"{amount} {dmg_typ_name} resistance from effect")
            if f"-{damage_type.get_display_name} Resist" in self.db.effects:
                amount = self.db.effects[f"-{dmg_typ_name} Resist"]["amount"]
                effect_resist -= amount
                if not quiet:
                    self.location.more_info(f"{amount} {dmg_typ_name} resistance from effect")

        return base_resist + dt_resist + eq_resist + effect_resist

    def get_max(self, stat_input):
        stats = {"HP": self.db.max_hp, "Stamina": self.db.max_stam, "Mana": self.db.max_mana}
        for i_stat in stats:
            if i_stat.lower().startswith(stat_input):
                stat = i_stat

        base = stats[stat]

        effect = 0
        if "Max " + stat in self.db.effects:
            effect = self.db.effects["Max " + stat]["amount"]

        return base + effect

    def get_regen(self, stat_input):
        stats = {"HP": self.db.hp_regen, "Stamina": self.db.stam_regen, "Mana": self.db.mana_regen}
        for i_stat in stats:
            if i_stat.lower().startswith(stat_input):
                stat = i_stat

        base = stats[stat]

        effect = Dec(0)
        if "+" + stat + " Regen" in self.db.effects:
            effect = Dec(self.db.effects[f"+{stat} Regen"]["amount"])
        if "-" + stat + " Regen" in self.db.effects:
            effect = Dec(self.db.effects[f"-{stat} Regen"]["amount"])

        return base + effect

    def get_defeat_xp(self):
        return 5

    def speed(self):
        """How many squares this character can move per 1 AP spent."""
        speed = self.get_attr("dexterity") // 3
        if self.effect_active("Slowed"):
            speed = speed // 2

        if speed < 1:
            speed = 1
        return speed

    # </editor-fold>

    def update_base_stats(self):
        """Recalculates derived stats like max hp and base evasion."""
        self.db.max_hp = MAX_HP_BASE + LVL_TO_MAXHP[self.db.level] + CON_TO_MAXHP[
            self.get_attr("con")]
        self.db.max_stam = MAX_STAM_BASE + LVL_TO_MAXSTAM[self.db.level] + STR_TO_MAXSTAM[
            self.get_attr("str")]
        self.db.max_mana = MAX_MANA_BASE + LVL_TO_MAXMANA[self.db.level] + SPIRIT_TO_MAXMANA[
            self.get_attr("spi")]

        self.db.char_defense[None] = CON_TO_DEFENSE[self.get_attr("con")]
        self.db.char_evasion = DEXT_TO_EVADE[self.get_attr("dex")]
        self.db.char_resistance[None] = WIS_TO_RESIST[self.get_attr("wis")]

    def cap_stats(self):
        """Ensure entity's hp, mana, and stamina are not greater than their maximum set values, or less than 0."""
        if self.db.hp > self.get_max("hp"):
            self.db.hp = self.get_max("hp")
        if self.db.mana > self.get_max("mana"):
            self.db.mana = self.get_max("mana")
        if self.db.stamina > self.get_max("stam"):
            self.db.stamina = self.get_max("stam")

        if self.db.hp < 0:
            self.db.hp = 0
        if self.db.mana < 0:
            self.db.mana = 0
        if self.db.stamina < 0:
            self.db.stamina = 0

    # </editor-fold>

    def knows_ability(self, ability):
        if not isinstance(ability, type):
            ability = type(ability)

        known_ability_types = [type(known_ability) for known_ability in self.db.abilities]
        if ability in known_ability_types:
            return True
        else:
            return False

    # <editor-fold desc="Effects">
    def effect_active(self, effect_key, duration_for_reset=0):
        """If this entity currently has this effect, returns the corresponding script. If this entity does not already
        have an effect with the given key, returns False."""
        for script in self.scripts.all():
            if script.db.effect_key == effect_key:
                return script
        return False

    def add_effect(self, typeclass=EffectScript, attributes=None, quiet=False, stack=False):
        """Adds or resets an effect with the given typeclass and attributes."""
        if not attributes:  # If attributes not given in call
            attributes = []  # Make sure initialized as a list
        if hasattr(typeclass, "fixed_attributes"):  # If typeclass has fixed attributes, like always the same duration
            attributes.extend(typeclass.fixed_attributes)

        # Extract effect key and duration for effect_active check
        for attribute in attributes:
            if attribute[0] == "effect_key":
                effect_key = attribute[1]
            elif attribute[0] == "duration":
                duration = attribute[1]
            elif attribute[0] == "amount":
                amount = attribute[1]
            elif attribute[0] == "source":
                source = attribute[1]

        script = self.effect_active(effect_key)
        if script:  # If this effect is already active on this entity
            if stack:
                self.db.effects[effect_key]["amount"] += amount
                return
            else:
                self.effect_active(effect_key).reset_seconds(duration)  # Restart timer, with this version's duration
                script.db.source = source
                self.location.msg_contents(f"{self.get_display_name(capital=True)} regains {script.color()}{effect_key}.")
                return

        # Create effect script attached to this entity
        effect = evennia.create_script(typeclass=typeclass, obj=self, attributes=attributes, key=effect_key)
        effect.pre_effect_add()  # Call pre_effect_add on the effect script
        if not quiet:
            self.location.msg_contents(f"{self.get_display_name(capital=True)} gains {effect.color()}{effect_key}.")

    def apply_effects(self):
        """Apply/increment all active effect scripts on this entity."""
        for script in self.scripts.all():
            if inherits_from(script, DurationEffect):
                try:
                    script.apply(in_combat=self.is_in_combat())
                except TypeError:
                    pass
        if self.is_in_combat():
            tile_effects = self.db.combat_turnhandler.db.grid.effects_at(self.db.combat_x, self.db.combat_y)
            for eff in tile_effects:
                eff.apply_to(self)

    # </editor-fold>

    # <editor-fold desc="Combat handling">
    def combat_symbol(self):
        return self.color() + self.name[0] + "|n"

    def is_in_combat(self):
        """Returns true if this entity is currently in combat."""
        try:
            if self.db.combat_turnhandler.is_in_combat(self):
                return True
            else:
                return False
        except AttributeError:
            return False

    def is_turn(self):
        """Returns true if this entity is in combat and it is currently this entity's turn."""
        try:
            if self.db.combat_turnhandler.is_turn(self):
                return True
            else:
                return False
        except AttributeError:
            return False

    def at_pre_move(self, destination, move_type="move", **kwargs):
        """
        Called just before starting to move this object to
        destination.

        Args:
            destination (Object): The object we are moving to

        Returns:
            shouldmove (bool): If we should move or not.

        Notes:
            If this method returns False/None, the move is cancelled
            before it is even started.

        """
        # A combination of this override and the direction commands is necessary to get the combat version of the
        # movement commands to execute whether there is a valid room exit found or not.
        exts = [ext for ext in self.location.exits if ext.destination == destination]
        if not exts:
            return True
        ext = exts[0]
        if self.is_in_combat():
            turn_handler = self.db.combat_turnhandler
            turn_handler.db.grid.step(obj=self, direction=ext.key[0])
            turn_handler.turn_end_check(self)
            return False
        if self.db.HP <= 0:
            self.msg("You can't move, you've been defeated!")
            return False
        return True

    def attack(self, target):
        weapon = self.get_weapon()
        if not COMBAT.check_range(self, target, weapon):
            return

        start_join_fight(self, target, weapon)
        COMBAT.resolve_attack(self, target, attack=weapon)

        # Unless that ends the fight, spend an action
        if self.is_in_combat():
            self.db.combat_turnhandler.spend_action(self, self.ap_to_attack(), action_name="attack")

    def apply_damage(self, damages):
        """
        Applies damage to a target, reducing their HP by the damage amount to a
        minimum of 0.

        Args:
            damages (dict): Types and amounts of damage being taken
        """
        for damage_type in damages:
            self.db.hp -= damages[damage_type]  # Reduce defender's HP by the damage dealt.

        # If this reduces it to 0 or less, set HP to 0.
        self.check_zero_hp()

    def check_zero_hp(self):
        """Triggers defeat at 0 hp, and ensures hp does not fall below 0."""
        if self.db.hp <= 0:
            self.db.hp = 0
            if self.is_in_combat():
                self.db.combat_turnhandler.at_defeat(defeated=self)
            else:
                self.at_defeat()

    def at_defeat(self):
        """Called when entity is defeated. This is a method on entities instead of the combat handler so that it can
        be overridden with different behavior by different kinds of entities."""
        self.location.msg_contents("|w|[110%s has been defeated!" % self.get_display_name(capital=True, color=False,
                                                                                          article=True))
        # End all timed buffs and debuffs
        for script in self.scripts.all():
            if inherits_from(script, DurationEffect):
                script.delete()
        self.update_base_stats()

        if self.db.dies:
            make_corpse(self)
            set_to_respawn(self)
        else:
            pass  # Be knocked out

        enemies = COMBAT.get_enemies(self)
        # Quest stages tied to killing this specific entity
        hooks = self.db.quest_hooks["at_defeat"]
        for qid in hooks:
            for stage in hooks[qid]:
                hook_data = hooks[qid][stage]
                for enemy in enemies:
                    if enemy.attributes.has("quest_stages") and enemy.quests.at_stage(qid, stage):
                        enemy.msg(hook_data["msg"])
                        enemy.quests.advance_quest(hook_data["next_stage"])

        # Quest stages tied to killing a number of enemies of a type
        for enemy in enemies:
            if not inherits_from(enemy, "typeclasses.living.players.PlayerCharacter"):
                continue
            kill_counters = enemy.db.kill_counters

            for i, kill_counter in enumerate(kill_counters):
                # Increment kill counter if defeated entity is of target type
                enemy_type = kill_counter["target_type"]
                if inherits_from(self, enemy_type):
                    enemy.db.kill_counters[i]["killed"] += 1

                # Check if kill counter has been filled, and advance to next stage if so
                if kill_counter["killed"] >= kill_counter["needed"]:
                    stage_desc = quest_desc(qid=kill_counter["QID"], stage=kill_counter["stage"])
                    enemy.msg(f"{appearance.notify}You have completed: {stage_desc}!")
                    stage_str = kill_counters[i]["next_stage"]
                    enemy.quests.advance_quest(stage_str)

        return True
    # </editor-fold>
    # TODO: Effect handler?
