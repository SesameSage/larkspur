"""
Characters

Characters are (by default) Objects setup to be puppeted by Accounts.
They are what you "see" in game. The Character class in this module
is set up to be the "default" character type created by the default
creation commands.

"""
from decimal import Decimal as Dec

from evennia.utils import make_iter

from commands.character_cmdsets import PlayerCmdSet
from commands.refiled_cmds import RefiledCmdSet
from typeclasses.inanimate import rooms
from typeclasses.inanimate.items.items import Item
from typeclasses.living.living_entities import *
from typeclasses.living.talking_npc import TalkableNPC

# TODO: Command Stats

XP_THRESHOLDS = {
    2: 100
}

BASE_CARRY_WEIGHT = Dec(30)
STR_TO_CARRY_WEIGHT = {
    1: Dec(0),
    2: Dec(5),
    3: Dec(10),
    4: Dec(20),
    5: Dec(35),
    6: Dec(55),
    7: Dec(80),
}
BASE_CARRY_COUNT = 10
DEX_TO_CARRY_COUNT = {
    1: 0,
    2: 2,
    3: 3,
    4: 5,
    5: 7,
    6: 10,
}


class Character(LivingEntity):
    """
    The Character just re-implements some of the Object's methods and hooks
    to represent a Character entity in-game.

    See mygame/typeclasses/objects.py for a list of
    properties and methods available on all Object child classes like this.

    """

    def at_object_creation(self):
        super().at_object_creation()
        self.db.appear_string = f"{self.name} is here."

    def color(self):
        return appearance.character

    def say(self, msg):
        self.at_say(message=msg, msg_self=True)

    def at_say(self, message, msg_self=None, msg_location=None, receivers=None, msg_receivers=None, **kwargs):
        # Overridden formatting
        """
        Display the actual say (or whisper) of self.

        This hook should display the actual say/whisper of the object in its
        location.  It should both alert the object (self) and its
        location that some text is spoken.  The overriding of messages or
        `mapping` allows for simple customization of the hook without
        re-writing it completely.

        Args:
            message (str): The message to convey.
            msg_self (bool or str, optional): If boolean True, echo `message` to self. If a string,
                return that message. If False or unset, don't echo to self.
            msg_location (str, optional): The message to echo to self's location.
            receivers (DefaultObject or iterable, optional): An eventual receiver or receivers of the
                message (by default only used by whispers).
            msg_receivers(str): Specific message to pass to the receiver(s). This will parsed
                with the {receiver} placeholder replaced with the given receiver.
        Keyword Args:
            whisper (bool): If this is a whisper rather than a say. Kwargs
                can be used by other verbal commands in a similar way.
            mapping (dict): Pass an additional mapping to the message.

        Notes:


            Messages can contain {} markers. These are substituted against the values
            passed in the `mapping` argument.
            ::

                msg_self = 'You say: "{speech}"'
                msg_location = '{object} says: "{speech}"'
                msg_receivers = '{object} whispers: "{speech}"'

            Supported markers by default:

            - {self}: text to self-reference with (default 'You')
            - {speech}: the text spoken/whispered by self.
            - {object}: the object speaking.
            - {receiver}: replaced with a single receiver only for strings meant for a specific
              receiver (otherwise 'None').
            - {all_receivers}: comma-separated list of all receivers,
              if more than one, otherwise same as receiver
            - {location}: the location where object is.

        """
        msg_type = "say"

        if kwargs.get("whisper", False):
            # whisper mode

            msg_type = "whisper"
            msg_self = (appearance.whisper +
                        '{self} whisper to {all_receivers}' + appearance.whisper + ': {speech}'
                        if msg_self is True
                        else msg_self
                        )
            msg_receivers = msg_receivers or '{object}' + appearance.whisper + ' whispers: {speech}'
            msg_receivers = appearance.whisper + msg_receivers
            msg_location = None
        else:
            msg_self = appearance.say + '{self} say: {speech}' if msg_self is True else msg_self
            msg_location = msg_location or '{object}' + appearance.say + ' says: {speech}'
            msg_receivers = msg_receivers or message
            msg_receivers = appearance.say + msg_receivers

        custom_mapping = kwargs.get("mapping", {})
        receivers = make_iter(receivers) if receivers else None
        location = self.location

        if msg_self:
            self_mapping = {
                "self": "You",
                "object": self.get_display_name(self),
                "location": location.get_display_name(self) if location else None,
                "receiver": None,
                "all_receivers": (
                    ", ".join(recv.get_display_name(self) for recv in receivers)
                    if receivers
                    else None
                ),
                "speech": message,
            }
            self_mapping.update(custom_mapping)
            self.msg(text=(msg_self.format_map(self_mapping), {"type": msg_type}), from_obj=self)

        if receivers and msg_receivers:
            receiver_mapping = {
                "self": "You",
                "object": None,
                "location": None,
                "receiver": None,
                "all_receivers": None,
                "speech": message,
            }
            for receiver in make_iter(receivers):
                individual_mapping = {
                    "object": self.get_display_name(receiver),
                    "location": location.get_display_name(receiver),
                    "receiver": receiver.get_display_name(receiver),
                    "all_receivers": (
                        ", ".join(recv.get_display_name(recv) for recv in receivers)
                        if receivers
                        else None
                    ),
                }
                receiver_mapping.update(individual_mapping)
                receiver_mapping.update(custom_mapping)
                receiver.msg(
                    text=(msg_receivers.format_map(receiver_mapping), {"type": msg_type}),
                    from_obj=self,
                )

        if self.location and msg_location:
            location_mapping = {
                "self": "You",
                "object": self,
                "location": location,
                "all_receivers": ", ".join(str(recv) for recv in receivers) if receivers else None,
                "receiver": None,
                "speech": message,
            }
            location_mapping.update(custom_mapping)
            exclude = []
            if msg_self:
                exclude.append(self)
            if receivers:
                exclude.extend(receivers)
            self.location.msg_contents(
                text=(msg_location, {"type": msg_type}),
                from_obj=self,
                exclude=exclude,
                mapping=location_mapping,
            )


class PlayerCharacter(Character):
    def at_object_creation(self):
        super().at_object_creation()
        self.permissions.add("Player")

        self.db.xp = 0
        self.db.portal_keys = []

        self.db.carry_weight = BASE_CARRY_WEIGHT
        self.db.max_carry_count = BASE_CARRY_COUNT
        # TODO: Story point and portal key handler

        self.attributes.add(key="prefs", value={"more_info": False}, category="ooc")

        self.cmdset.add(PlayerCmdSet, persistent=True)
        self.cmdset.add(RefiledCmdSet, persistent=True)  # Override player cmds where necessary

    def update_stats(self):
        super().update_stats()
        self.db.carry_weight = BASE_CARRY_WEIGHT + STR_TO_CARRY_WEIGHT[self.get_attr("str")]

    def color(self):
        return appearance.player

    def at_look(self, target=None, session=None, **kwargs):
        if isinstance(target, rooms.Room):
            self.execute_cmd("map")
        return super().at_look(target, **kwargs)

    def cmd_format(self, string):
        return appearance.cmd + "'" + string + "'|n"

    def print_ambient(self, string):
        self.msg(appearance.ambient + string)

    def print_hint(self, string):
        self.msg(appearance.hint + "Hint: " + string)

    def more_info(self, string):
        if self.attributes.get("prefs", category="ooc")["more_info"]:
            self.msg(appearance.moreinfo + string)

    def gain_xp(self, amt):
        self.db.xp += amt
        self.msg(f"You gain {amt} experience.")
        if self.db.xp >= XP_THRESHOLDS[(self.db.level + 1)]:
            self.level_up()

    def level_up(self):
        self.update_stats()

    def encumbrance(self):
        encumbrance = Dec(0)
        for item in self.contents:
            if isinstance(item, Item):
                if item.contents:
                    for content in item.contents:
                        encumbrance += content.db.weight
                encumbrance += item.db.weight

        return encumbrance

    def carried_count(self):
        carried_count = 0
        for item in self.contents:
            if isinstance(item, Item):
                carried_count += 1
        return carried_count


class NPC(Character, TalkableNPC):
    pass


class EnemyCharacter(Enemy, NPC):
    pass
