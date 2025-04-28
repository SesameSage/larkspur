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

from commands.character_cmdsets import PlayerCmdSet
from commands.refiled_cmds import RefiledCmdSet
from typeclasses.inanimate.locations import rooms
from typeclasses.living.char_stats import xp_threshold
from typeclasses.living.enemies import Enemy
from typeclasses.living.living_entities import *
from typeclasses.living.talking_npc import TalkableNPC
from typeclasses.scripts.player_scripts import LevelUpReminder


class Character(LivingEntity):
    """
    A sentient living thing that can speak.
    """

    def at_object_creation(self):
        super().at_object_creation()
        self.db.appear_string = f"{self.get_display_name()} is here."

    def color(self):
        return appearance.character

    def say(self, msg):
        self.at_say(message=msg, msg_self=True)

    def say_to(self, character, msg):
        self.at_say(message=msg, receivers=character)

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
            msg_self = self.get_display_name(
                capital=True) + appearance.say + ' say: {speech}' if msg_self is True else msg_self
            msg_location = msg_location or self.get_display_name(capital=True) + appearance.say + ' says: {speech}'
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
    """A character intended to be played by a user. """

    def at_object_creation(self):
        super().at_object_creation()
        self.db.unique_name = True
        self.permissions.add("Player")
        self.db.dies = False

        if not self.attributes.has("xp"):
            self.db.xp = 0
        if not self.attributes.has("attr_points"):
            self.db.attr_points = 0

        if not self.attributes.has("portal_keys"):
            self.db.portal_keys = []

        self.db.carry_weight = BASE_CARRY_WEIGHT
        self.db.max_carry_count = BASE_CARRY_COUNT
        # TODO: Story point and portal key handler

        if not self.attributes.has("prefs", category="ooc"):
            self.attributes.add(key="prefs", value={"more_info": False}, category="ooc")

        self.cmdset.add(PlayerCmdSet, persistent=True)
        self.cmdset.add(RefiledCmdSet, persistent=True)  # Override player cmds where necessary

        self.update_base_stats()

    def update_base_stats(self):
        super().update_base_stats()
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
        if self.db.xp >= xp_threshold(self.db.level + 1):
            self.scripts.add(LevelUpReminder())

    def level_up(self):
        self.update_base_stats()

    def meets_level_requirement(self, target):
        # Abilities
        if target.db.cooldown:
            ability_tree = self.db.rpg_class.ability_tree
            for level in range(self.db.level + 1):
                if level == 0:
                    continue
                if type(target) in ability_tree[level]:
                    return True
            return False

    def meets_attr_requirements(self, target):
        # Abilities
        if target.db.cooldown:
            for stat, amount in target.db.requires:
                # Use the base character attribute, not the effective value from equipment, etc
                if self.db.attribs[stat] < amount:
                    return False
            return True


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
        table = EvTable("Item", "Type", "Cost")
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
        table = EvTable("Ability", "Cost")
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


class EnemyCharacter(Enemy, NPC):
    pass
