from evennia import Command
from evennia.commands.default.muxcommand import MuxCommand
from evennia.utils.create import create_object

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
    key = "moreinfo"
    help_category = "appearance"

    def func(self):
        self.caller.attributes.get("prefs", category="ooc")["more_info"] = \
            not self.caller.attributes.get("prefs", category="ooc")["more_info"]
        self.caller.print_ambient(
            f"MoreInfo set to {self.caller.attributes.get("prefs", category="ooc")["more_info"]}.")


class CmdHere(Command):
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
    key = "classes"
    switch_options = ("add", "remove")
    help_category = "character"

    def func(self):
        trainer = None
        for obj in self.caller.location.contents:
            if obj.attributes.has("classes"):
                trainer = obj
                break
        if not trainer:
            self.caller.msg("No one to train with here!")
            return

        if "add" in self.switches:
            if not self.caller.permissions.check("Builder"):
                self.caller.msg("Only builders can alter class lists!")
            else:
                if not self.lhs:
                    self.caller.msg("Add what ability?")
                    return
                elif not self.rhs:
                    self.caller.msg(f"Remember to include class cost! {appearance.cmd}classes/add <ability> = <price>")
                    return
                else:
                    try:
                        cost = int(self.rhs)
                    except ValueError:
                        self.caller.msg("Couldn't interpret  " + self.rhs + " as an integer.")
                        return

                    ability_input = self.lhs
                    ability = all_abilities.get(ability_input)
                    if not ability:
                        self.caller.msg("No ability found for " + ability_input)
                        return

                    obj = create_object(typeclass=ability, key=ability.key, location=trainer)

                    trainer.db.classes[obj] = cost
                    self.caller.msg(f"Successfully added {ability.key} as a class taught by {trainer.name}.")
        elif "remove" in self.switches:
            if not self.caller.permissions.check("Builder"):
                self.caller.msg("Only builders can alter class lists!")
            else:
                if not self.lhs:
                    self.caller.msg("Remove what class?")
                    return
                class_input = self.lhs
                clss = all_abilities.get(class_input)
                if not clss:
                    self.caller.msg("No ability found for " + class_input)
                    return
                key = clss.key if isinstance(clss.key, str) else clss.__name__
                if clss not in [type(ability) for ability in trainer.db.classes]:
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

        else:
            show_all = False
            if self.lhs and self.lhs == "all":
                show_all = True

            trainer.display_classes(self.caller, show_all)


class CmdLearn(MuxCommand):
    key = "learn"
    help_category = "character"

    def func(self):
        if not self.lhs:
            self.caller.msg("Learn which ability?")
            self.caller.execute_cmd("classes")
            return
        else:
            ability_input = self.lhs

        trainer = None
        for obj in self.caller.location.contents:
            if obj.attributes.has("classes"):
                trainer = obj
                break
        if not trainer:
            self.caller.msg("No one here to learn from!")
            return

        target_ability = None
        for ability in trainer.db.classes:
            if ability.key.lower().startswith(ability_input.lower()):
                target_ability = ability
                break
        if not target_ability:
            self.caller.msg("No class here found for " + ability_input)
            return

        if not self.caller.is_correct_class(target_ability):
            self.caller.msg("You are not the right class to learn this ability!")
            return
        if not self.caller.meets_level_requirement(target_ability):
            self.caller.msg("You must attain more knowledge and experience as a " + self.caller.db.rpg_class.key +
                            "before you are ready to take this class.")
            return
        obj = create_object(typeclass=type(target_ability), key=target_ability.key, location=self.caller)
        self.caller.db.abilities.append(obj)
        self.caller.msg(f"{trainer.name} teaches you to use {obj.get_display_name()}!")


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

        self.add(CmdTravel)
        self.add(CmdIdentify)
        self.add(CmdBuy)
        self.add(CmdShop)
