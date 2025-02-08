"""
Characters

Characters are (by default) Objects setup to be puppeted by Accounts.
They are what you "see" in game. The Character class in this module
is set up to be the "default" character type created by the default
creation commands.

"""
from server import appearance
from typeclasses.inanimate import rooms
from typeclasses.living.living_entities import *
from evennia.contrib.game_systems.clothing import ClothedCharacter
from evennia.contrib.tutorials.talking_npc import TalkingNPC


class Character(LivingEntity, ClothedCharacter):
    """
    The Character just re-implements some of the Object's methods and hooks
    to represent a Character entity in-game.

    See mygame/typeclasses/objects.py for a list of
    properties and methods available on all Object child classes like this.

    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def at_look(self, target=None, session=None, **kwargs):
        if isinstance(target, rooms.Room):
            self.execute_cmd("map")
        return super().at_look(target, **kwargs)

    def get_display_name(self, looker=None, **kwargs):
        return appearance.character + super().get_display_name(looker=looker) + "|n"


class PlayerCharacter(Character):

    def get_display_name(self, looker=None, **kwargs):
        return appearance.player + super().get_display_name(looker=looker)[4:] + "|n"

    def cmd_format(self, string):
        return appearance.cmd + "'" + string + "'|n"

    def print_ambient(self, string):
        self.msg(appearance.ambient + string)

    def print_hint(self, string):
        self.msg(appearance.hint + "Hint: " + string)


class NPC(Character, TalkingNPC):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def say(self, msg):
        room = self.location
        characters = room.contents_get(content_type="character")
        for character in characters:
            character.msg(f"{self.get_display_name(looker=character)}{appearance.say}: {msg}")


