import time
from evennia import CmdSet, Command

from server import appearance
from typeclasses.inanimate.exits import Door
from typeclasses.scripts.scene import Scene

global lofthus


class CmdKnock(Command):
    key = "knock"

    def func(self):
        door = None
        rm = self.caller.location
        for rm_exit in rm.exits:
            if isinstance(rm_exit, Door):
                for alias in rm_exit.aliases.all():
                    if self.args.strip() == alias:
                        door = rm_exit
        if not door:
            self.caller.msg(f"No door found matching '{self.args}'")
        else:
            self.caller.db.knocked_doors.add(door)
            self.caller.print_ambient("You pound on the door to awaken and alarm your neighbors.")


class KnockCmdSet(CmdSet):
    def at_cmdset_creation(self):
        self.add(CmdKnock)


class GameStartScene(Scene):

    def at_script_creation(self):
        self.key = "GameStartScene"
        self.repeats = 0

        global lofthus
        lofthus = self.obj.search("lofthus", global_search=True)
        outside_your_home = self.obj.search("Outside your home", global_search=True)
        if lofthus.location != outside_your_home:
            lofthus.move_to(outside_your_home)

        self.obj.print_ambient("You awaken to the smell of putrid smoke, and have a feeling something is very wrong.")
        self.obj.print_hint(self.obj.cmd_format("get lantern"))
        self.obj.scripts.add(LeaveBedroomScene())
        self.delete()


class LeaveBedroomScene(Scene):
    def at_script_creation(self):
        self.key = "LeaveBedroomScene"
        self.interval = 0.1

    def at_repeat(self, **kwargs):
        bedroom = self.obj.search("Your bedroom", global_search=True)
        time.sleep(2)
        if self.obj.location != bedroom:
            self.obj.print_ambient(
                "A red-hot flickering glow bleeds into your home. With alarm, you notice smoke pouring in "
                "from underneath the front door. So the fire isn't in the house itself... at least, not yet.")
            self.obj.scripts.add(LeaveHomeScene())
            self.delete()


class LeaveHomeScene(Scene):

    def at_script_creation(self):
        self.key = "LeaveHomeScene"
        self.interval = 4
        self.home = self.obj.search("Your home", global_search=True)
        global lofthus
        self.spoken_lines = iter(
            ["You there - We've been attacked! The town guard has nearly fallen. We're evacuating to the north!",
             f"They cut the alarm bells - "
             f"please, as you go, {appearance.cmd}knock{appearance.say} on as many doors as you can!",
             f"We've got to alert everyone and get them out!",
             "I'm going to circle around this block first. Although I couldn't ask it of you, "
             "I can cover you if you choose to help."])

    def at_repeat(self, **kwargs):
        if self.obj.location != self.home:
            line = next(self.spoken_lines, None)
            if not line:
                self.obj.cmdset.add(KnockCmdSet)
                self.obj.db.knocked_doors = set()
                self.obj.print_hint(f"{appearance.cmd}knock east")

                exit = self.obj.search("south")
                lofthus.move_to(exit)
                self.obj.scripts.add(ChoosePathScene())
                self.delete()
            else:
                lofthus.say(line)


class ChoosePathScene(Scene):
    def at_script_creation(self):
        self.key = "ChoosePathScene"
        self.interval = 1

    def at_repeat(self, **kwargs):
        if self.obj.location == self.obj.search("Down the south path", global_search=True):
            time.sleep(1)
            global lofthus
            lofthus.say("I'm grateful Napasso has brave citizens like you. Let's press on quickly - stay behind me, and"
                        "if things get sticky for me, don't hesitate to run back north. Any number we can save is worth"
                        " the fight.")
            self.obj.scripts.add(FollowLofthusScene())
            self.delete()


class FollowLofthusScene(Scene):
    def at_script_creation(self):
        self.key = "FollowLofthusScene"
        self.interval = 3
        global lofthus

    def at_repeat(self, **kwargs):
        doors = [exit for exit in lofthus.location.exits if "home" in exit.name]
        if all(door in self.obj.db.knocked_doors for door in doors):
            south = self.obj.search("south")
            lofthus.move_to(south)
