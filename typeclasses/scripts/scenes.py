import time

import evennia.utils
from typing_extensions import Iterator

from server import appearance
from typeclasses.scripts.scripts import Script


class Scene(Script):
    pass


class GameStartScene(Scene):

    def at_script_creation(self):
        self.key = "GameStartScene"
        self.repeats = 0
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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def at_script_creation(self):
        self.key = "LeaveHomeScene"
        self.interval = 3
        self.home = self.obj.search("Your home", global_search=True)
        self.lofthus = self.obj.search("lof", global_search=True)
        self.spoken_lines = iter(["You there!", "We've been attacked. The town guard has fallen.",
                             f"We're evacuating to the north - "
                             f"please, as you go, {appearance.cmd}knock{appearance.say} on as many doors as you can!",
                             "I'm going to circle around this block first. Although I couldn't ask it of you, "
                             "I can cover you if you choose to do the same."])

    def at_repeat(self, **kwargs):
        if self.obj.location != self.home:
            line = next(self.spoken_lines, None)
            if not line:
                exit = self.obj.search("south")
                self.lofthus.move_to(exit)
                self.delete()
            else:
                self.lofthus.say(line)
