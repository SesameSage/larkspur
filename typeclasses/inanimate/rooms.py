from collections import defaultdict

from evennia.objects.objects import DefaultRoom
from evennia.utils import iter_to_str

from server import appearance
from typeclasses.base.objects import Object, Fixture


# TODO: Areas, Regions
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
        self.db.region = None

        self.db.is_outdoors = True
        self.db.environment = None

    appearance_template = """
{header}
|350{name}{extra_name_info}|n
{desc}
{footer}
{characters}
{things}
{exits}
        """

    def get_display_footer(self, looker, **kwargs):
        fixtures = self.filter_visible([content for content in self.contents if isinstance(content, Fixture)], looker, **kwargs)
        string = ""
        first_line = True
        for fixture in fixtures:
            if first_line:
                string = "|244" + fixture.db.desc
                first_line = False
            else:
                string = string + "\n" + fixture.db.desc
        return string

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
                string = character.color() + character.db.appear_string
            else:
                string = string + "\n" + character.db.appear_string

        return string

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
        exit_names = (appearance.exit + exi.get_display_name(looker, **kwargs) for exi in exits)
        exit_names = iter_to_str(_sort_exit_names(exit_names))

        return f"|wExits:|n {exit_names}" if exit_names else ""

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

    def more_info(self, string):
        for thing in self.contents:
            try:
                thing.more_info(string)
            except AttributeError:
                pass

    def print_ambient(self, string):
        self.msg_contents(appearance.ambient + string)

