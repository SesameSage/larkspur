from collections import defaultdict

from evennia.objects.objects import DefaultRoom
from evennia.utils import iter_to_str, is_iter, make_iter, lazy_property

from server import appearance
from server.appearance import ENVIRONMENTS_BY_TYPE
from server.funcparser import MyFuncParser, MY_ACTOR_STANCE_CALLABLES
from typeclasses.base.objects import Object
from typeclasses.inanimate.fixtures import Fixture, Fountain, Well
from typeclasses.scripts.weather import RAINING

_MSG_CONTENTS_PARSER = MyFuncParser(MY_ACTOR_STANCE_CALLABLES)


class Room(Object, DefaultRoom):
    """
    Rooms are like any Object, except their location is None
    (which is default). They also use basetype_setup() to
    add locks so they cannot be puppeted or picked up.
    (to change that, use at_object_creation instead)

    See mygame/typeclasses/objects.py for a list of
    properties and methods available on all Objects.
    """

    def at_object_creation(self):
        self.db.area = None
        self.db.coordinates = ()

        self.db.is_outdoors = True
        self.db.environment = None

        self.db.current_weather = None

        self.db.quest_hooks = {"at_object_receive": {}}

    def at_object_delete(self):
        # Remove this room from the area containing it
        if self.db.area:
            self.db.area.db.rooms.remove(self)
        return True

    def at_object_receive(self, moved_obj, source_location, move_type="move", **kwargs):
        super().at_object_receive(moved_obj, source_location, move_type, **kwargs)
        hooks = self.db.quest_hooks["at_object_receive"]
        for qid in hooks:
            for stage in hooks[qid]:
                hook_data = hooks[qid][stage]
                if moved_obj.attributes.has("quest_stages") and moved_obj.quests.at_stage(qid, stage):
                    moved_obj.msg(hook_data["msg"])
                    moved_obj.quests.advance_quest(hook_data["next_stage"])

    # <editor-fold desc="Properties">
    @lazy_property
    def x(self):
        return self.db.coordinates[0]

    @lazy_property
    def y(self):
        return self.db.coordinates[1]

    @lazy_property
    def z(self):
        return self.db.coordinates[2]

    # These methods jump up the location hierarchy tree.
    def locality(self):
        if self.db.area:
            return self.db.area.db.locality

    def zone(self):
        if self.locality():
            return self.locality().db.zone

    def region(self):
        if self.zone():
            return self.zone().db.region

    def has_water(self):
        if self.db.environment in ENVIRONMENTS_BY_TYPE["water"]:
            return True

        if self.in_room(Fountain):
            return True

        well = self.in_room(Well)
        if well and not well.db.empty:
            return True

        if self.db.current_weather == RAINING:
            return True

        return False
    # </editor-fold>

    # <editor-fold desc="Display">
    # Changes to order and color
    appearance_template = """
{header}
|331{name}{extra_name_info}|n
{desc}
{footer}
{characters}
{things}
{exits}
        """

    def get_display_footer(self, looker, **kwargs):
        """Describes room fixtures like portals."""
        fixtures = self.filter_visible([content for content in self.contents if isinstance(content, Fixture)], looker,
                                       **kwargs)
        string = ""
        first_line = True
        for fixture in fixtures:
            if first_line:
                string = "|244" + fixture.db.desc + "|n"
                first_line = False
            else:
                string = string + "\n" + fixture.db.desc + "|n"
        return string

    # Overridden to use each character's appear_string
    def get_display_characters(self, looker, **kwargs):
        """
        Get the 'characters' component of the object description. Called by `return_appearance`.

        Args:
            looker (DefaultObject): Object doing the looking.
            **kwargs: Arbitrary data for use when overriding.
        Returns:
            str: The character display data.

        """
        characters = self.filter_visible(
            self.contents_get(content_type="character"), looker, **kwargs
        )
        string = ""
        first_line = True
        for character in characters:
            if first_line:
                string = character.db.appear_string
                first_line = False
            else:
                string = string + "\n" + character.db.appear_string

        return string

    # Overridden to add color
    def get_display_exits(self, looker, **kwargs):
        """
        Get the 'exits' component of the object description. Called by `return_appearance`.

        Args:
            looker (DefaultObject): Object doing the looking.
            **kwargs: Arbitrary data for use when overriding.

        Keyword Args:
            exit_order (iterable of str): The order in which exits should be listed, with
                unspecified exits appearing at the end, alphabetically.

        Returns:
            str: The exits display data.

        Examples:
        ::

            For a room with exits in the order 'portal', 'south', 'north', and 'out':
                obj.get_display_name(looker, exit_order=('north', 'south'))
                    -> "Exits: north, south, out, and portal."  (markup not shown here)
        """

        def _sort_exit_names(names):
            exit_order = kwargs.get("exit_order")
            if not exit_order:
                return names
            sort_index = {name: key for key, name in enumerate(exit_order)}
            names = sorted(names)
            end_pos = len(sort_index)
            names.sort(key=lambda name: sort_index.get(name, end_pos))
            return names

        exits = self.filter_visible(self.contents_get(content_type="exit"), looker, **kwargs)

        # Check if player can move in every lateral direction, so exit names can be condensed
        all_lateral_directions = False
        all_exit_names = [ex.name for ex in exits]
        directions = ["north", "south", "east", "west", "northwest", "northeast", "southwest", "southeast"]
        if all(direction in all_exit_names for direction in directions):
            all_lateral_directions = True
            exits = [ex for ex in exits if ex.name not in directions]

        exit_names = [appearance.exit + exi.get_display_name(looker, **kwargs) for exi in exits]
        if all_lateral_directions:
            exit_names.append(appearance.exit + "all lateral directions")
        exit_names = iter_to_str(_sort_exit_names(exit_names))

        return f"|wExits:|n {exit_names}" if exit_names else ""

    # Overridden to exclude Fixtures
    def get_display_things(self, looker, **kwargs):
        """
        Get the 'things' component of the object description. Called by `return_appearance`.

        Args:
            looker (DefaultObject): Object doing the looking.
            **kwargs: Arbitrary data for use when overriding.
        Returns:
            str: The things display data.

        """
        # sort and handle same-named things
        things = self.filter_visible(self.contents_get(content_type="object"), looker, **kwargs)

        grouped_things = defaultdict(list)
        for thing in things:
            if not isinstance(thing, Fixture):
                grouped_things[thing.get_display_name(looker, **kwargs)].append(thing)

        thing_names = []
        for thingname, thinglist in sorted(grouped_things.items()):
            nthings = len(thinglist)
            thing = thinglist[0]
            singular, plural = thing.get_numbered_name(nthings, looker, key=thingname)
            thing_names.append(thing.color() + singular + "|n" if nthings == 1 else thing.color() + plural + "|n")
        thing_names = iter_to_str(thing_names)
        return f"|wYou see:|n {thing_names}" if thing_names else ""

    def room_appearance(self):
        """Gets the dictionary containing the background, foreground, and player colors for this room's environment."""
        if not self.db.environment:
            return

        for i_colortype in ENVIRONMENTS_BY_TYPE:
            if self.db.environment in ENVIRONMENTS_BY_TYPE[i_colortype]:
                return appearance.ENV_TYPES_APPEAR[i_colortype]

    # </editor-fold>

    # <editor-fold desc="Messaging">
    def more_info(self, string):
        """Prints combat calculation info to any players here if they have moreinfo enabled."""
        for thing in self.contents:
            try:
                thing.more_info(string)
            except AttributeError:
                pass

    def print_ambient(self, string):
        self.msg_contents(appearance.ambient + string)

    # Overridden to replace funcparser with ours that uses custom capitalization logic
    def msg_contents(
            self,
            text=None,
            exclude=None,
            from_obj=None,
            mapping=None,
            raise_funcparse_errors=False,
            **kwargs,
    ):
        """
        Emits a message to all objects inside this object.

        Args:
            text (str or tuple): Message to send. If a tuple, this should be
                on the valid OOB outmessage form `(message, {kwargs})`,
                where kwargs are optional data passed to the `text`
                outputfunc. The message will be parsed for `{key}` formatting and
                `$You/$you()/$You()`, `$obj(name)`, `$conj(verb)` and `$pron(pronoun, option)`
                inline function callables.
                The `name` is taken from the `mapping` kwarg {"name": object, ...}`.
                The `mapping[key].get_display_name(looker=recipient)` will be called
                for that key for every recipient of the string.
            exclude (list, optional): A list of objects not to send to.
            from_obj (Object, optional): An object designated as the
                "sender" of the message. See `DefaultObject.msg()` for
                more info. This will be used for `$You/you` if using funcparser inlines.
            mapping (dict, optional): A mapping of formatting keys
                `{"key":<object>, "key2":<object2>,...}.
                The keys must either match `{key}` or `$You(key)/$you(key)` markers
                in the `text` string. If `<object>` doesn't have a `get_display_name`
                method, it will be returned as a string. Pass "you" to represent the caller,
                this can be skipped if `from_obj` is provided (that will then act as 'you').
            raise_funcparse_errors (bool, optional): If set, a failing `$func()` will
                lead to an outright error. If unset (default), the failing `$func()`
                will instead appear in output unparsed.

            **kwargs: Keyword arguments will be passed on to `obj.msg()` for all
                messaged objects.

        Notes:
            For 'actor-stance' reporting (You say/Name says), use the
            `$You()/$you()/$You(key)` and `$conj(verb)` (verb-conjugation)
            inline callables. This will use the respective `get_display_name()`
            for all onlookers except for `from_obj or self`, which will become
            'You/you'. If you use `$You/you(key)`, the key must be in `mapping`.

            For 'director-stance' reporting (Name says/Name says), use {key}
            syntax directly. For both `{key}` and `You/you(key)`,
            `mapping[key].get_display_name(looker=recipient)` may be called
            depending on who the recipient is.

        Examples:

            Let's assume:

            - `player1.key` -> "Player1",
            - `player1.get_display_name(looker=player2)` -> "The First girl"
            - `player2.key` -> "Player2",
            - `player2.get_display_name(looker=player1)` -> "The Second girl"

            Actor-stance:
            ::

                char.location.msg_contents(
                    "$You() $conj(attack) $you(defender).",
                    from_obj=player1,
                    mapping={"defender": player2})

            - player1 will see `You attack The Second girl.`
            - player2 will see 'The First girl attacks you.'

            Director-stance:
            ::

                char.location.msg_contents(
                    "{attacker} attacks {defender}.",
                    mapping={"attacker":player1, "defender":player2})

            - player1 will see: 'Player1 attacks The Second girl.'
            - player2 will see: 'The First girl attacks Player2'

        """
        # we also accept an outcommand on the form (message, {kwargs})
        is_outcmd = text and is_iter(text)
        inmessage = text[0] if is_outcmd else text
        outkwargs = text[1] if is_outcmd and len(text) > 1 else {}
        mapping = mapping or {}
        you = from_obj or self

        if "you" not in mapping:
            mapping["you"] = you

        contents = self.contents
        if exclude:
            exclude = make_iter(exclude)
            contents = [obj for obj in contents if obj not in exclude]

        for receiver in contents:
            # actor-stance replacements
            outmessage = _MSG_CONTENTS_PARSER.parse(
                inmessage,
                raise_errors=raise_funcparse_errors,
                return_string=True,
                caller=you,
                receiver=receiver,
                mapping=mapping,
            )

            # director-stance replacements
            outmessage = outmessage.format_map(
                {
                    key: (
                        obj.get_display_name(looker=receiver)
                        if hasattr(obj, "get_display_name")
                        else str(obj)
                    )
                    for key, obj in mapping.items()
                }
            )

            receiver.msg(text=(outmessage, outkwargs), from_obj=from_obj, **kwargs)

    # </editor-fold>

    def in_room(self, typeclass: type):
        """Returns the first object of the given type found in this room."""
        for content in self.contents:
            if isinstance(content, typeclass):
                return content

    def update_weather(self, weather):
        """Messages characters here about the new weather."""
        self.db.current_weather = weather
        self.print_ambient(weather["start_msg"])
        if weather["effect"]:
            pass
