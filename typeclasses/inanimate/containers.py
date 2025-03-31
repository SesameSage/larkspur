"""
Containers

Contribution by InspectorCaracal (2023)

Adds the ability to put objects into other container objects by providing a container typeclass and extending certain base commands.

To install, import and add the `ContainerCmdSet` to `CharacterCmdSet` in your `default_cmdsets.py` file:

    from evennia.contrib.game_systems.containers import ContainerCmdSet

    class CharacterCmdSet(default_cmds.CharacterCmdSet):
        # ...

        def at_cmdset_creation(self):
            # ...
            self.add(ContainerCmdSet)

The ContainerCmdSet includes:

 - a modified `look` command to look at or inside objects
 - a modified `get` command to get objects from your location or inside objects
 - a new `put` command to put objects from your inventory into other objects

Create objects with the `ContribContainer` typeclass to easily create containers,
or implement the same locks/hooks in your own typeclasses.

`ContribContainer` implements the following new methods:

    at_pre_get_from(getter, target, **kwargs) - called with the pre-get hooks
    at_pre_put_in(putter, target, **kwargs)   - called with the pre-put hooks
"""
from collections import defaultdict

from django.conf import settings
from evennia import AttributeProperty, CmdSet, DefaultObject, EvTable
from evennia.commands.default.general import CmdDrop, CmdGet, CmdLook
from evennia.utils import class_from_module

from server import appearance
from typeclasses.base.objects import Object
from typeclasses.inanimate.items.items import Item

# establish the right inheritance for container objects
_BASE_OBJECT_TYPECLASS = class_from_module(settings.BASE_OBJECT_TYPECLASS, DefaultObject)


class Container(Item):
    """
    A type of Object which can be used as a container.

    It implements a very basic "size" limitation that is just a flat number of objects.
    """

    def at_object_creation(self):
        """
        Extends the base object `at_object_creation` method by setting the "get_from" lock to "true",
        allowing other objects to be put inside and removed from this object.

        By default, a lock type not being explicitly set will fail access checks, so objects without
        the new "get_from" access lock will fail the access checks and continue behaving as
        non-container objects.
        """
        super().at_object_creation()
        self.db.desc = "A container to hold items."
        self.db.capacity = None
        self.locks.add("get_from:true()")

    def color(self):
        return appearance.container

    def at_pre_get_from(self, getter, target, **kwargs):
        """
        This will be called when something attempts to get another object FROM this object,
        rather than when getting this object itself.

        Args:
            getter (Object): The actor attempting to take something from this object.
            target (Object): The thing this object contains that is being removed.

        Returns:
            boolean: Whether the object `target` should be gotten or not.

        Notes:
            If this method returns False/None, the getting is cancelled before it is even started.
        """
        return True

    def at_pre_put_in(self, putter, target, **kwargs):
        """
        This will be called when something attempts to put another object into this object.

        Args:
            putter (Object): The actor attempting to put something in this object.
            target (Object): The thing being put into this object.

        Returns:
            boolean: Whether the object `target` should be put down or not.

        Notes:
            If this method returns False/None, the putting is cancelled before it is even started.
            To add more complex capacity checks, modify this method on your child typeclass.
        """
        # check if we're already at capacity
        if len(self.contents) >= self.db.capacity:
            singular, _ = self.get_numbered_name(1, putter)
            putter.msg(f"You can't fit anything else in {singular}.")
            return False

        return True

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
            grouped_things[thing.get_display_name(looker, **kwargs)].append(thing)

        thing_names = []
        for thingname, thinglist in sorted(grouped_things.items()):
            nthings = len(thinglist)
            thing = thinglist[0]
            singular, plural = thing.get_numbered_name(nthings, looker, key=thingname)
            thing_names.append(singular if nthings == 1 else plural)
        # thing_names = iter_to_str(thing_names)
        table = EvTable(f"|wInside {self.get_display_name(looker=looker)}:", border=None, )
        for thing_name in thing_names:
            table.add_row(thing_name)
        return table if thing_names else f"{appearance.ambient}{self.name.capitalize()} contains nothing you can see."


class CmdContainerLook(CmdLook):
    """
    look at location or object

    Usage:
      look                      (Look around at your location.)
      look <obj>                (Look at an object.)
      look in <container>       (Look at what's inside.)
      look <obj> in <container> (Look at an object inside a container.)
      look *<account>

    Observes your location or objects in your vicinity.
    """

    rhs_split = (" in ",)
    help_category = "navigation"

    def func(self):
        """
        Handle the looking.
        """
        caller = self.caller
        # by default, we don't look in anything
        container = None

        if not self.args:
            target = caller.location
            if not target:
                self.msg("You have no location to look at!")
                return
        else:
            if self.rhs:
                # we are looking in something, find that first
                container = caller.search(self.rhs)
                if not container:
                    return

            viewing_all = False
            if self.lhs.startswith("in "):
                lhs = self.lhs[3:]
                viewing_all = True
            else:
                lhs = self.lhs
            target = caller.search(lhs, location=container)
            if not target:
                return
            if viewing_all:
                self.msg(target.get_display_things(looker=caller))
                return
        desc = caller.at_look(target)
        # add the type=look to the outputfunc to make it
        # easy to separate this output in client.
        self.msg(text=(desc, {"type": "look"}), options=None)


class CmdContainerGet(CmdGet):
    """
    pick up something

    Usage:
      get <obj>
      get <obj> from <container>

    Picks up an object from your location or a container and puts it in
    your inventory.
    """

    rhs_split = (" from ",)
    help_category = "items"

    def func(self):
        caller = self.caller
        # by default, we get from the caller's location
        location = caller.location

        if not self.args:
            self.msg("Get what?")
            return

        # check for a container as the location to get from
        if self.rhs:
            location = caller.search(self.rhs)
            if not location:
                return
            # check access lock
            if not location.access(caller, "get_from"):
                # supports custom error messages on individual containers
                if location.db.get_from_err_msg:
                    self.msg(location.db.get_from_err_msg)
                else:
                    self.msg("You can't get things from that.")
                return

        obj = caller.search(self.lhs, location=location)
        if not obj:
            return
        if caller == obj:
            self.msg("You can't get yourself.")
            return

        # check if this object can be gotten
        if not obj.access(caller, "get") or not obj.at_pre_get(caller):
            if obj.db.get_err_msg:
                self.msg(obj.db.get_err_msg)
            else:
                self.msg("You can't get that.")
            return
        if self.caller.encumbrance() + obj.db.weight > self.caller.db.carry_weight:
            self.msg("You can't carry that much!")
            return
        if self.caller.carried_count() + 1 > self.caller.db.max_carry_count:
            self.msg("You can't carry that many items!")
            return

        # calling possible at_pre_get_from hook on location
        if hasattr(location, "at_pre_get_from") and not location.at_pre_get_from(caller, obj):
            self.msg("You can't get that.")
            return

        success = obj.move_to(caller, quiet=True, move_type="get")
        if not success:
            self.msg("This can't be picked up.")
        else:
            singular, _ = obj.get_numbered_name(1, caller)
            if location == caller.location:
                # we're picking it up from the area
                caller.location.msg_contents(f"$You() $conj(pick) up {singular}.", from_obj=caller)
            else:
                # we're getting it from somewhere else
                container_name, _ = location.get_numbered_name(1, caller)
                caller.location.msg_contents(
                    f"$You() $conj(get) {singular} from {container_name}.", from_obj=caller
                )
            # calling at_get hook method
            obj.at_get(caller)


class CmdPut(CmdDrop):
    """
    put an object into something else

    Usage:
      put <obj> in <container>

    Lets you put an object from your inventory into another
    object in the vicinity.
    """

    key = "put"
    rhs_split = (" in ", "=", " on ")

    def func(self):
        caller = self.caller
        if not self.args:
            self.msg("Put what in where?")
            return

        if not self.rhs:
            super().func()
            return

        obj = caller.search(
            self.lhs,
            location=caller,
            nofound_string=f"You aren't carrying {self.args}.",
            multimatch_string=f"You carry more than one {self.args}:",
        )
        if not obj:
            return

        container = caller.search(self.rhs)
        if not container:
            return

        # check access lock
        if not container.access(caller, "get_from"):
            # supports custom error messages on individual containers
            if container.db.put_err_msg:
                self.msg(container.db.put_err_msg)
            else:
                self.msg("You can't put things in that.")
            return

        # Call the object script's at_pre_drop() method.
        if not obj.at_pre_drop(caller):
            self.msg("You can't put that down.")
            return

        # Call the container's possible at_pre_put_in method.
        if hasattr(container, "at_pre_put_in") and not container.at_pre_put_in(caller, obj):
            self.msg("You can't put that there.")
            return

        success = obj.move_to(container, quiet=True, move_type="drop")
        if not success:
            self.msg("This couldn't be dropped.")
        else:
            obj_name, _ = obj.get_numbered_name(1, caller)
            container_name, _ = container.get_numbered_name(1, caller)
            caller.location.msg_contents(
                f"$You() $conj(put) {obj_name} in {container_name}.", from_obj=caller
            )
            # Call the object script's at_drop() method.
            obj.at_drop(caller)


class ContainerCmdSet(CmdSet):
    """
    Extends the basic `look` and `get` commands to support containers,
    and adds an additional `put` command.
    """

    key = "Container CmdSet"
    help_category = "items"

    def at_cmdset_creation(self):
        super().at_cmdset_creation()

        self.add(CmdContainerLook)
        self.add(CmdContainerGet)
        self.add(CmdPut)
