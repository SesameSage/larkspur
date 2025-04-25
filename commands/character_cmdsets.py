from evennia import Command
from evennia.commands.default.muxcommand import MuxCommand
from evennia.utils.create import create_object
from evennia.utils.evtable import EvTable

from combat.abilities import all_abilities
from commands.permissions_cmdsets import BuildingCmdSet
from commands.refiled_cmds import *
from server import appearance
from typeclasses.inanimate.items.containers import ContainerCmdSet
from typeclasses.inanimate.items.items import CmdIdentify, CmdBuy, CmdShop
from typeclasses.inanimate.portals import CmdTravel
from typeclasses.living.char_stats import StatsCmdSet
from typeclasses.living.talking_npc import TalkingCmdSet


class CmdMoreInfo(Command):
    """
        toggle seeing real-time combat calculations

        Usage:
          moreinfo

        This command changes the moreinfo preference for this character.
        Setting moreinfo to True displays an array of faded messages
        on the status of calculations in combat.
        """
    key = "moreinfo"
    help_category = "appearance"

    def func(self):
        self.caller.attributes.get("prefs", category="ooc")["more_info"] = \
            not self.caller.attributes.get("prefs", category="ooc")["more_info"]
        self.caller.print_ambient(
            f"MoreInfo set to {self.caller.attributes.get("prefs", category="ooc")["more_info"]}.")


class CmdHere(Command):
    """
        see info on your location

        Usage:
          here

        The "here" command shows your current room's area, locality,
        zone, and region.
        """
    key = "here"
    help_category = "navigation"

    def func(self):
        room = self.caller.location
        area = room.db.area.key if room.db.area else "None"
        locality = room.locality().key if room.locality() else "None"
        zone = room.zone().key if room.zone() else "None"
        region = room.region().key if room.region() else "None"

        self.caller.msg(f"|wRoom:|n {room.get_display_name()}\n"
                        f"|wArea:|n {area}\n"
                        f"|wLocality:|n {locality}\n"
                        f"|wZone:|n {zone}\n"
                        f"|wRegion:|n {region}\n")


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
        trainer = None
        for obj in self.caller.location.contents:
            if obj.attributes.has("classes"):
                trainer = obj
                break
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

        # Check character's eligibility to learn
        if not self.caller.is_correct_class(target_ability):
            self.caller.msg("You are not the right class to learn this ability!")
            return
        if not self.caller.meets_level_requirement(target_ability):
            self.caller.msg("You must attain more knowledge and experience as a " + self.caller.db.rpg_class.key +
                            "before you are ready to take this class.")
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
        table = EvTable()
        for ability in self.caller.db.abilities:
            ellips = False
            desc = ability.db.desc
            if len(desc) > 45:
                desc = desc[:45] + "..."
            table.add_row(ability.get_display_name(), desc, f"cost: {ability.db.cost[1]} {ability.db.cost[0]}")
        self.caller.msg(table)


class PlayerCmdSet(CmdSet):
    key = "DefaultCharacter"

    def at_cmdset_creation(self):
        super().at_cmdset_creation()
        self.add(BuildingCmdSet)
        self.add(TalkingCmdSet)
        self.add(ContainerCmdSet)
        self.add(StatsCmdSet)

        self.add(CmdMoreInfo)
        self.add(CmdHere)
        self.add(CmdClasses)
        self.add(CmdLearn)
        self.add(CmdSpells)

        self.add(CmdTravel)
        self.add(CmdIdentify)
        self.add(CmdBuy)
        self.add(CmdShop)
