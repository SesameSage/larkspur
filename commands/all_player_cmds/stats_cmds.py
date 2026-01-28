from evennia import Command, CmdSet
from evennia.commands.default.muxcommand import MuxCommand
from evennia.utils.create import create_object
from evennia.utils.evtable import EvTable

from combat.abilities import all_abilities
from combat.abilities.spells import Spell
from combat.effects import DamageTypes
from server import appearance
from stats.char_stats import xp_remaining, xp_threshold, level_up
from typeclasses.living.characters import Trainer


class CmdClasses(MuxCommand):
    """
        view and edit class lists on trainer NPCs

        Usage:
          classes

          (Builders only)
            classes/add <ability name> = <cost>
            classes/remove <ability name>

        NPCs capable of training the player in abilities and/or spells
        will display their available classes to normal players, formatted
        based on the player's eligibility to learn each ability.

        Builders have the additional option to add and remove classes
        from the list.
        """
    key = "classes"
    switch_options = ("add", "remove", "cost")
    help_category = "character"

    def func(self):
        # Find the trainer in the room
        trainer = self.caller.location.in_room(Trainer)
        if not trainer:
            self.caller.msg("No one to train with here!")
            return

        # If using a switch to attempt to alter class list
        if len(self.switches) > 0:
            # Check that caller has permission
            if not self.caller.permissions.check("Builder"):
                self.caller.msg("Only builders can alter class lists!")
                return

            # Get ability name input
            if not self.lhs:
                self.caller.msg("What ability?")
                return
            ability_input = self.lhs

            # Find ability class
            ability = all_abilities.get(ability_input)
            if not ability:
                self.caller.msg("No ability found for " + ability_input)
                return

            # Get ability key
            key = ability.key if isinstance(ability.key, str) else ability.__name__

        # Standard command for non-builders (display classes)
        else:
            show_all = False
            if self.lhs and self.lhs == "all":
                show_all = True

            trainer.display_classes(self.caller, show_all)
            return

        # Builder options
        if "add" in self.switches:
            if not self.rhs:
                self.caller.msg(f"Remember to include class cost! {appearance.cmd}classes/add <ability> = <price>")
                return
            else:
                try:
                    cost = int(self.rhs)
                except ValueError:
                    self.caller.msg("Couldn't interpret  " + self.rhs + " as an integer.")
                    return

                # Give an instance of the ability to the trainer
                obj = create_object(typeclass=ability, key=key, location=trainer)

                # Add the abiltiy and its cost to the trainer's class list
                trainer.db.classes[obj] = cost
                self.caller.msg(f"Successfully added {key} as a class taught by {trainer.name}.")

        elif "remove" in self.switches:
            if not ability:
                self.caller.msg("No ability found for " + ability_input)
                return
            if ability not in trainer.abilities_taught():
                self.caller.msg(f"{trainer.name} doesn't seem to teach {key}.")
                return

            ability_obj = trainer.search(key)
            del trainer.db.classes[ability_obj]
            try:
                trainer.db.classes[ability_obj]
                self.caller.msg("Class removal was not successful.")
                return
            except KeyError:
                self.caller.msg("Class successfully removed.")
            if ability_obj.delete():
                self.caller.msg("Successfully deleted ability object.")

        elif "cost" in self.switches:
            if not self.rhs:
                self.caller.msg(f"Remember to include class cost! {appearance.cmd}classes/cost <ability> = <price>")
                return
            if ability not in trainer.abilities_taught():
                self.caller.msg(f"{trainer.name} doesn't seem to teach {key}.")
            else:
                try:
                    cost = int(self.rhs)
                except ValueError:
                    self.caller.msg("Couldn't interpret  " + self.rhs + " as an integer.")
                    return

                ability_obj = trainer.search(key)
                if not ability_obj:
                    self.caller.msg("Couldn't find ability object in trainer's contents.")
                    return
                trainer.db.classes[ability_obj] = cost
                if trainer.db.classes[ability_obj] == cost:
                    self.caller.msg("Successfully changed class cost for " + key)


class CmdLearn(MuxCommand):
    """
        learn a spell or ability you are eligible for

        Usage:
          learn <ability name>

        Examples:
            learn firebolt
            learn blinding beam

        Any abilities in your class's ability tree up to your level
        can be learned from a trainer, as long as the trainer teaches
        a class in that ability.
        """
    key = "learn"
    help_category = "character"

    def func(self):
        # Get ability input
        if not self.lhs:
            self.caller.msg("Learn which ability?")
            self.caller.execute_cmd("classes")
            return
        else:
            ability_input = self.lhs

        # Find a trainer in the room
        trainer = None
        for obj in self.caller.location.contents:
            if obj.attributes.has("classes"):
                trainer = obj
                break
        if not trainer:
            self.caller.msg("No one here to learn from!")
            return

        # Find a matching ability taught here
        target_ability = None
        for ability in trainer.db.classes:
            if ability.key.lower().startswith(ability_input.lower()):
                target_ability = ability
                break
        if not target_ability:
            self.caller.msg("No class here found for " + ability_input)
            return

        ability_or_spell = "spell" if isinstance(ability, Spell) else "ability"

        # Check character's eligibility to learn
        if self.caller.knows_ability(target_ability):
            self.caller.msg(f"You already know this {ability_or_spell}!")
            return
        if not target_ability.in_ability_tree(self.caller.db.rpg_class):
            self.caller.msg(f"You are not the right class to learn this {ability_or_spell}!")
            return
        if not self.caller.meets_level_requirement(target_ability):
            self.caller.msg("You must attain more knowledge and experience as a " + self.caller.db.rpg_class.key +
                            "before you are ready to take this class.")
            return
        for stat, amount in target_ability.db.requires:
            # Use the base character attribute, not the effective value from equipment, etc
            if self.caller.db.attribs[stat] < amount:
                self.caller.msg(f"Your {stat.capitalize()} isn't high enough!")
                return

        # Check the character has enough gold
        cost = trainer.db.classes[target_ability]
        if self.caller.db.gold < cost:
            self.caller.msg("You don't have enough gold!")
            return

        # Create and add ability
        obj = create_object(typeclass=type(target_ability), key=target_ability.key, location=self.caller)
        self.caller.db.abilities.append(obj)
        self.caller.msg(f"{trainer.name} teaches you to use {obj.get_display_name()}!")

        # Deduct cost
        self.caller.db.gold -= cost


class CmdSpells(Command):
    """
        see your spells and abilities

        Usage:
          spells
          spel
          sp
          abilities
          abil
          ab

        All spells and abilities that you have learned will display here.
        To cast a spell or ability, use 'cast <ability> <target>' (if the
        ability must have a target) or 'cast <ability>' otherwise.
        """
    key = "spells"
    aliases = ("spell", "spel", "sp", "abilities", "abil", "ab")
    help_category = "character"

    def func(self):
        current_spells = EvTable(pretty_corners=True)
        for ability in self.caller.db.abilities:
            desc = ability.desc
            if len(desc) > 50:
                desc = desc[:48] + "..."
            current_spells.add_row(ability.get_display_name(), desc, f"|wCosts|n: {ability.cost_string()}")

        available_spells = EvTable(pretty_corners=True)
        for level in range(self.caller.db.level + 1):
            if level == 0:
                continue
            for ability in self.caller.db.rpg_class.ability_tree[level]:
                if not self.caller.knows_ability(ability):
                    color = appearance.spell if isinstance(ability, Spell) else appearance.ability
                    available_spells.add_row(color + ability.key, ability.desc)

        self.caller.msg("|wYour abilities:")
        self.caller.msg(current_spells)
        self.caller.msg("")
        self.caller.msg("|wAbilities you can currently learn:")
        self.caller.msg(available_spells)


class CmdHP(Command):
    """
        show current hitpoints

        Usage:
          hp (my hp)
          hp <entity>

        Get a combat entity's current hitpoints.
        Hitpoints are analogous to health or life. You are defeated when your hp falls to zero.
        """
    key = "hp"
    help_category = "stats"

    def func(self):
        if self.args:  # Target given
            target = self.caller.search(
                self.args, candidates=[content for content in self.caller.location.contents if content.db.hp])
            if not target:
                self.caller.msg(f"Can't find '{self.args}' here")
                return
            if not target.db.hp:
                self.caller.msg(f"{target.name.capitalize()} doesn't have hitpoints!")
                return
            self.caller.msg(f"{target.name.capitalize()}'s HP: {appearance.hp}{target.db.hp}|n / {target.db.max_hp}")
        else:  # Show self HP
            self.caller.msg(f"Your HP: {appearance.hp}{self.caller.db.hp}|n / {self.caller.db.max_hp}")


class CmdMana(Command):
    """
        show current mana

        Usage:
          mana (my stamina)
          mana <entity>

        Get a combat entity's current mana.
        Mana is a resource used to cast spells."""
    key = "mana"
    aliases = "man"
    help_category = "stats"

    def func(self):
        if self.args:  # Target given
            target = self.caller.search(
                self.args, candidates=[content for content in self.caller.location.contents if content.db.mana])
            if not target:
                self.caller.msg(f"Can't find '{self.args}' here")
                return
            if not target.db.mana:
                self.caller.msg(f"{target.name.capitalize()} doesn't have mana!")
                return
            self.caller.msg(f"{target.name.capitalize()}'s mana: "
                            f"{appearance.mana}{target.db.mana}|n / {target.db.max_mana}")
        else:  # Show self mana
            self.caller.msg(f"Your mana: {appearance.mana}{self.caller.db.mana}|n / {self.caller.db.max_mana}")


class CmdStamina(Command):
    """
    show current stamina

    Usage:
      stamina (my stamina)
      stamina <entity>

    Get a combat entity's current stamina.
    Stamina is a resource used for physical abilities such as Sweep and Shield Bash.
    """
    key = "stamina"
    aliases = "stam"
    help_category = "stats"

    def func(self):
        if self.args:  # Target given
            target = self.caller.search(
                self.args,
                candidates=[content for content in self.caller.location.contents if content.attributes.has("stamina")])
            if not target:
                self.caller.msg(f"Can't find '{self.args}' here")
                return
            if not target.db.stamina:
                self.caller.msg(f"{target.name.capitalize()} doesn't have stamina!")
                return
            self.caller.msg(f"{target.name.capitalize()}'s stamina: "
                            f"{appearance.stamina}{target.db.stamina}|n / {target.db.max_stam}")
        else:  # Show self stamina
            self.caller.msg(f"Your stamina: {appearance.stamina}{self.caller.db.stamina}|n / {self.caller.db.max_stam}")


class CmdStats(Command):
    """
    show a combat entity's stats

    Usage:
      stats (your stats)
      stats <entity>

    Prints a table showing a combat entity's stats, such as hitpoints and strength.

    Values such as resistance and constitution display the active value first, taking
    equipment and effects into account, then display the base character value in parentheses.
    """
    key = "stats"
    aliases = "stat"
    help_category = "stats"

    def func(self):

        def display_resistances(target):
            string = ""

            # Display base character defense, evasion, and resistance
            stat_mapping = {target.get_defense: target.db.char_defense[None] if None in target.db.char_defense else 0,
                            target.get_evasion: target.db.char_evasion,
                            target.get_resistance: target.db.char_resistance[
                                None] if None in target.db.char_resistance else 0}
            for stat_func in stat_mapping:
                string = string + f"{appearance.highlight}{stat_func(quiet=True)}|n "
                try:
                    char_stat = stat_mapping[stat_func]
                except KeyError:
                    char_stat = 0
                string = string + f"({char_stat})\n"

            # Add separation and extra line to align with "Resists:" subheader
            string = string + "\n\n"

            # Display specific resistances
            for damage_type in DamageTypes:

                if damage_type in [DamageTypes.BLUNT, DamageTypes.SLASHING, DamageTypes.PIERCING]:
                    stat = target.db.char_defense
                    stat_method = target.get_defense
                elif damage_type in [DamageTypes.FIRE, DamageTypes.COLD, DamageTypes.SHOCK, DamageTypes.POISON]:
                    stat = target.db.char_resistance
                    stat_method = target.get_resistance

                string = string + f"{appearance.highlight}{stat_method(damage_type, type_only=True, quiet=True)}|n "
                try:
                    char_stat = stat[damage_type]
                except KeyError:
                    char_stat = 0
                string = string + f"({char_stat})\n"

            return string

        if self.args:  # Target given
            target = self.caller.search(
                self.args,
                candidates=[content for content in self.caller.location.contents if content.attributes.has("hp")])
            if not target:
                self.caller.msg(f"Can't find '{self.args}' here")
                return
            if not target.attributes.has("hp"):
                self.caller.msg(f"{target.name.capitalize()} doesn't have relevant stats!")
                return
        else:  # Show self stats
            target = self.caller

        table = EvTable(pretty_corners=True)
        table.add_column(f"Class:\n"
                         f"Level:\n"
                         f"HP:\n"
                         f"Mana:\n"
                         f"Stamina:\n\n"

                         f"Gold:\n"
                         f"Carried items:\n"
                         f"Carry weight:\n"
                         , header=f"{target.get_display_name(capital=True)}")

        try:
            class_name = target.db.rpg_class.name
        except AttributeError:
            class_name = ""
        table.add_column(f"{class_name}\n"
                         f"|w{target.db.level}|n\n"
                         f"{appearance.hp}{target.db.hp}/{target.get_max("hp")}|n\n"
                         f"{appearance.mana}{target.db.mana}/{target.get_max("mana")}|n\n"
                         f"{appearance.stamina}{target.db.stamina}/{target.get_max("stam")}|n\n\n"

                         f"{appearance.gold}{target.db.gold}|n\n"
                         f"{target.carried_count()}/{target.db.max_carry_count}\n"
                         f"{target.encumbrance()}/{target.db.carry_weight}\n")

        table.add_column(f"Strength:\n"
                         f"Constitution:\n"
                         f"Dexterity:\n"
                         f"Perception:\n"
                         f"Intelligence:\n"
                         f"Wisdom:\n"
                         f"Spirit:\n\n")
        table.add_column(f"{appearance.highlight}{target.get_attr("str")}|n ({target.db.attribs["strength"]})\n"
                         f"{appearance.highlight}{target.get_attr("con")}|n ({target.db.attribs["constitution"]})\n"
                         f"{appearance.highlight}{target.get_attr("dex")}|n ({target.db.attribs["dexterity"]})\n"
                         f"{appearance.highlight}{target.get_attr("per")}|n ({target.db.attribs["perception"]})\n"
                         f"{appearance.highlight}{target.get_attr("int")}|n ({target.db.attribs["intelligence"]})\n"
                         f"{appearance.highlight}{target.get_attr("wis")}|n ({target.db.attribs["wisdom"]})\n"
                         f"{appearance.highlight}{target.get_attr("spi")}|n ({target.db.attribs["spirit"]})\n\n")

        table.add_column(f"Defense:\n"
                         f"Evasion:\n"
                         f"Resistance:\n\n"

                         f"|wResists:|n\n"
                         f"|=oBlunt: \n"
                         f"|=oSlashing: \n"
                         f"|=oPiercing: \n"
                         f"|=oCrushing: \n"
                         f"|=oArcane: \n"
                         f"|=oFire: \n"
                         f"|=oCold: \n"
                         f"|=oShock: \n"
                         f"|=oPoison: \n")
        table.add_column(f"{display_resistances(target)}")

        self.caller.msg(table)


class CmdEffects(Command):
    """
        show active effects

        Usage:
          effects
          effects <entity>
          eff

        Show all effects (such as poisoned, regenerating, +Damage, etc.) currently active on you or a target entity.
        """
    key = "effects"
    aliases = "effect", "eff", "ef"
    help_category = "stats"

    def func(self):
        if self.args:  # Target given
            target = self.caller.search(
                self.args, candidates=[content for content in self.caller.location.contents if content.db.hp])
            if not target:
                self.caller.msg(f"Can't find '{self.args}' here")
                return
            if not target.attributes.has("effects"):
                self.caller.msg(f"{target.name.capitalize()} isn't affected by combat conditions!")
                return
        else:  # Show self effects
            target = self.caller

        table = EvTable("|wEffect", "|wAmount", "|wSource", "|wDuration")

        for effect in target.db.effects:
            name = effect
            effect = target.db.effects[effect]
            amount = effect["amount"] if "amount" in effect else "--"
            source = effect["source"].key
            duration = effect["duration"] if "duration" in effect else "-"
            seconds_passed = effect["seconds passed"] if "seconds passed" in effect else "-"
            table.add_row(name, amount, source, f"{seconds_passed}/{duration}")

        self.caller.msg(table)


class CmdAP(Command):
    """
        show current action points

        Usage:
          ap
          ap <entity>

        Get a combat entity's current AP.
        Action points (AP) are replenished every turn in battle and spent on actions like moving, attacking, using
        items, and casting spells.
        """
    key = "ap"
    help_category = "stats"

    def func(self):
        if self.args:  # Target given
            target = self.caller.search(
                self.args, candidates=[content for content in self.caller.location.contents if content.attributes.has("hp")])
            if not target:
                self.caller.msg(f"Can't find '{self.args}' here")
                return
            if not target.attributes.has("hp"):
                self.caller.msg(f"{target.name.capitalize()} doesn't have relevant stats!")
                return

        else:  # Show self stats
            target = self.caller

        if not target.is_in_combat():
            if target == self.caller:
                self.caller.msg(f"You aren't in combat!")
            else:
                self.caller.msg(f"{target.name.capitalize()} isn't in combat!")
            return

        self.caller.msg(f"{target.get_display_name(capital=True)} has {target.db.combat_ap} AP.")


class CmdXP(Command):
    """
        show current XP and next goal

        Usage:
          xp

        Show how much experience you have, and how much you need to gain before your next level-up.
        """
    key = "xp"
    help_category = "stats"

    def func(self):
        """
            show xp to next level

            Usage:
              xp

            Displays your total experience points gained, and your progress toward leveling up.
            """
        total = self.caller.db.xp
        next_level = self.caller.db.level + 1
        remaining = xp_remaining(self.caller, next_level)
        self.caller.msg(f"You have amassed {total} experience points.")
        self.caller.msg(f"You need {remaining} more XP to reach level {next_level}.")


class CmdLevelUp(Command):
    """
        increase character level if able

        Usage:
          level up
          level
          lev

        If you have enough experience, you can increase your character's experience level. Some of your stats will
        improve automatically, and others can be increased by spending points awarded on level-up.
        """
    key = "level up"
    aliases = "level", "lev"
    help_category = "character"

    def func(self):
        caller = self.caller
        if caller.db.xp < xp_threshold(caller.db.level + 1):
            caller.msg("You do not have enough experience to level up!")
            return
        else:
            level_up(caller)


class StatsCmdSet(CmdSet):
    key = "PlayerCharacter"

    def at_cmdset_creation(self):
        super().at_cmdset_creation()
        self.add(CmdHP)
        self.add(CmdMana)
        self.add(CmdStamina)
        self.add(CmdStats)
        self.add(CmdEffects)
        self.add(CmdAP)
        self.add(CmdXP)

        self.add(CmdClasses)
        self.add(CmdLearn)
        self.add(CmdSpells)

        self.add(CmdLevelUp)
