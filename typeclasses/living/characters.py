"""
Characters

Characters are (by default) Objects setup to be puppeted by Accounts.
They are what you "see" in game. The Character class in this module
is set up to be the "default" character type created by the default
creation commands.

"""

from evennia import EvTable
from evennia.prototypes.spawner import spawn
from evennia.utils import make_iter

from typeclasses.living.living_entities import *
from typeclasses.living.talking_npc import TalkableNPC


class Character(LivingEntity):
    """
    A sentient living thing that can speak.
    """

    def at_object_creation(self):
        super().at_object_creation()
        self.db.appear_string = f"{self.get_display_name()} is here."
        self.db.quest_hooks = {"at_talk": {}, "at_told": {}, "at_defeat": {}, "at_object_receive": {}}

    def color(self):
        return appearance.character

    def say(self, msg):
        self.at_say(message=msg, msg_self=True)

    def say_to(self, character, msg):
        self.at_say(message=msg, msg_location="$You() $conj(say) to " + character.get_display_name() + ": " +
                                              appearance.say + "{speech}")

    def at_object_receive(self, moved_obj, source_location, move_type="move", **kwargs):
        super().at_object_receive(moved_obj, source_location, move_type, **kwargs)
        for quest_hook in self.db.quest_hooks["at_object_receive"]:
            if source_location.attributes.has("quest_stages") and source_location.quests.at_stage(quest_hook):
                for line in quest_hook["spoken lines"]:
                    self.say_to(source_location, line)
                source_location.quests.advance_quest(quest_hook)

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
            msg_self = ("$You() $conj(whisper) to {all_receivers}': {speech}"
                        if msg_self is True
                        else msg_self
                        )
            msg_receivers = msg_receivers or '{object}' + appearance.whisper + ' whispers: {speech}'
            msg_receivers = appearance.whisper + msg_receivers
            msg_location = None

            self_mapping = {
                "self": "You",
                "object": self.get_display_name(self),
                "location": self.location.get_display_name(self) if self.location else None,
                "receiver": None,
                "all_receivers": (
                    ", ".join(recv.get_display_name(self) for recv in receivers)
                    if receivers
                    else None
                ),
                "speech": message,
            }
            self.msg(text=(msg_self.format_map(self_mapping), {"type": msg_type}), from_obj=self)
        else:
            msg_location = msg_location or self.color() + "$You()|n $conj(say): " + appearance.say + "{speech}"
            msg_receivers = msg_receivers or message
            msg_receivers = appearance.say + msg_receivers

        custom_mapping = kwargs.get("mapping", {})
        receivers = make_iter(receivers) if receivers else None
        location = self.location

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
            if receivers:
                exclude.extend(receivers)
            self.location.msg_contents(
                text=(msg_location, {"type": msg_type}),
                from_obj=self,
                exclude=exclude,
                mapping=location_mapping,
            )

    def at_talk(self, player):
        """
        If the player running the talk command is at the right quest stage for any at_talk hooks on this character, this
        character speaks some lines, and advances the player's quest afterward.

        :param player: The player running the talk command.
        """
        for quest_hook in self.db.quest_hooks["at_talk"]:
            if player.quests.at_stage(quest_hook):
                for line in quest_hook["spoken_lines"]:
                    self.say_to(player, line)
                player.quests.advance_quest(quest_hook)

    def at_tell(self, receiver, message: str):
        pass

    def at_told(self, teller, message: str):
        """
        Checks any at_told quest hooks on this character that the speaking player is at the right quest stage for.
        These quest hooks have dialogue choice 'options', usually multiple, with keywords that the player must say in
        their message to activate that option. Each option has its own spoken lines and points to its own next quest
        stage.

        :param teller:
        :param message:
        :return:
        """
        for quest_hook in self.db.quest_hooks["at_told"]:
            if teller.quests.at_stage(quest_hook):
                for option in quest_hook["options"]:
                    for keyword in option["keywords"]:
                        if keyword not in message.split(" "):  # Keyword missing from this dialogue option
                            continue  # Try the next option
                        else:  # All keywords in this dialogue option present in the message
                            for line in option["spoken lines"]:
                                self.say_to(teller, line)
                            teller.quests.advance_to(quest_hook["qid"], option["next_stage"])
                            return


class NPC(Character, TalkableNPC):
    pass


class Vendor(NPC):
    """An NPC who can sell items to players."""

    def at_object_creation(self):
        super().at_object_creation()
        self.db.unique_name = True
        self.db.dies = False
        self.db.stock = {}  # {Item: prototype_key}

    def add_to_stock(self, prototype_key):
        """Add a prototype to the vendor's wares."""
        item = spawn(prototype_key)[0]
        item.location = self
        item.locks.add("get:perm(developer)")
        self.db.stock[item] = prototype_key

    def display_stock(self, player):
        """Returns a table of items being sold by the vendor."""
        table = EvTable("Item", "Type", "Cost", pretty_corners=True)
        for item in self.db.stock:
            table.add_row(item.get_display_name(), item.__class__.__name__, appearance.gold + str(item.db.avg_value))
        player.msg(table)

    def sell_item(self, player, input):
        """Takes gold from a player, spawns one of the items selected, and gives it to the player."""
        stock_item = self.search(input, candidates=self.db.stock.keys())
        if not stock_item:
            return False
        if player.db.gold < stock_item.db.avg_value:
            self.say_to(player, "That's not enough gold for that item.")
            return False
        item_to_sell = spawn(self.db.stock[stock_item])[0]
        player.db.gold -= stock_item.db.avg_value
        self.db.gold += stock_item.db.avg_value
        item_to_sell.move_to(destination=player, quiet=True, move_type="purchase")
        singular = item_to_sell.get_numbered_name(count=1, looker=player)[0]
        player.msg("You receive " + singular + ".")


class Trainer(NPC):
    """An NPC who can teach the player abilities."""

    def at_object_creation(self):
        super().at_object_creation()
        self.db.unique_name = True
        self.db.dies = False
        self.db.classes = {}  # Ability, price

    def abilities_taught(self):
        return [type(ability) for ability in self.db.classes]

    def display_classes(self, player, show_all=False):
        table = EvTable("Ability", "Cost", pretty_corners=True)
        shown = []

        for ability in self.db.classes:
            if player.knows_ability(ability):
                if show_all:
                    color = "|=k"
                    shown.append((ability, color))
            elif player.meets_level_requirement(ability) and player.meets_attr_requirements(ability):
                color = "|450"
                shown.append((ability, color))
            elif ability.in_ability_tree(player.db.rpg_class):
                color = "|w"
                if show_all:
                    shown.append((ability, color))
            else:
                color = "|=k"
                if show_all:
                    shown.append((ability, color))

        for ability, color in shown:
            price = self.db.classes[ability]
            table.add_row(color + ability.key, appearance.gold + str(price))

        player.msg(f"{self.get_display_name(capital=True)} can teach:")
        player.msg(table)
