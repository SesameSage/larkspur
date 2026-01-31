from cmd import Cmd

from evennia.commands.cmdset import CmdSet
from evennia.commands.default.help import CmdSetHelp, HelpCategory, DEFAULT_HELP_CATEGORY, _loadhelp, _savehelp, \
    _quithelp
from evennia.commands.default.muxcommand import MuxCommand
from evennia.locks.lockhandler import LockException
from evennia.utils import inherits_from, create
from evennia.utils.create import create_object
from evennia.utils.eveditor import EvEditor

from combat.abilities import all_abilities
from combat.abilities.all_abilities import ALL_ABILITIES
from stats.combat_character import CombatEntity


# Overridden to automatically format help for spells/abilities
class MyCmdSetHelp(CmdSetHelp):
    def func(self):
        ability_input = self.lhs
        if ability_input in ALL_ABILITIES:
            obj = create_object(typeclass=ALL_ABILITIES[ability_input], key=ability_input)
            self.rhs = obj.get_help()
            obj.delete()

        switches = self.switches
        lhslist = self.lhslist
        rhslist = self.rhslist

        if not self.args:
            self.msg(
                "Usage: sethelp[/switches] <topic>[[;alias;alias][,category[,locks]] [= <text or new category>]"
            )
            return

        nlist = len(lhslist)
        topicstr = lhslist[0] if nlist > 0 else ""
        if not topicstr:
            self.msg("You have to define a topic!")
            return
        topicstrlist = topicstr.split(";")
        topicstr, aliases = (
            topicstrlist[0],
            topicstrlist[1:] if len(topicstr) > 1 else [],
        )
        aliastxt = ("(aliases: %s)" % ", ".join(aliases)) if aliases else ""
        old_entry = None

        # check if we have an old entry with the same name

        cmd_help_topics, db_help_topics, file_help_topics = self.collect_topics(
            self.caller, mode="query"
        )
        # db-help topics takes priority over file-help
        file_db_help_topics = {**file_help_topics, **db_help_topics}
        # commands take priority over the other types
        all_topics = {**file_db_help_topics, **cmd_help_topics}
        # get all categories
        all_categories = list(
            set(HelpCategory(topic.help_category) for topic in all_topics.values())
        )
        # all available help options - will be searched in order. We also check # the
        # read-permission here.
        entries = list(all_topics.values()) + all_categories

        # default setup
        category = lhslist[1] if nlist > 1 else DEFAULT_HELP_CATEGORY
        lockstring = ",".join(lhslist[2:]) if nlist > 2 else "read:all()"

        # search for existing entries of this or other types
        old_entry = None
        for querystr in topicstrlist:
            match, _ = self.do_search(querystr, entries)
            if match:
                warning = None
                if isinstance(match, HelpCategory):
                    warning = (
                        f"'{querystr}' matches (or partially matches) the name of "
                        f"help-category '{match.key}'. If you continue, your help entry will "
                        "take precedence and the category (or part of its name) *may* not "
                        "be usable for grouping help entries anymore."
                    )
                elif inherits_from(match, "evennia.commands.command.Command"):
                    warning = (
                        f"'{querystr}' matches (or partially matches) the key/alias of "
                        f"Command '{match.key}'. Command-help take precedence over other "
                        "help entries so your help *may* be impossible to reach for those "
                        "with access to that command."
                    )
                elif inherits_from(match, "evennia.help.filehelp.FileHelpEntry"):
                    warning = (
                        f"'{querystr}' matches (or partially matches) the name/alias of the "
                        f"file-based help topic '{match.key}'. File-help entries cannot be "
                        "modified from in-game (they are files on-disk). If you continue, "
                        "your help entry may shadow the file-based one's name partly or "
                        "completely."
                    )
                if warning:
                    # show a warning for a clashing help-entry type. Even if user accepts this
                    # we don't break here since we may need to show warnings for other inputs.
                    # We don't count this as an old-entry hit because we can't edit these
                    # types of entries.
                    self.msg(f"|rWarning:\n|r{warning}|n")
                    repl = yield ("|wDo you still want to continue? Y/[N]?|n")
                    if repl.lower() in ("y", "yes"):
                        # find a db-based help entry if one already exists
                        db_topics = {**db_help_topics}
                        db_categories = list(
                            set(HelpCategory(topic.help_category) for topic in db_topics.values())
                        )
                        entries = list(db_topics.values()) + db_categories
                        match, _ = self.do_search(querystr, entries)
                        if match:
                            old_entry = match
                    else:
                        self.msg("Aborted.")
                        return
                else:
                    # a db-based help entry - this is OK
                    old_entry = match
                    category = lhslist[1] if nlist > 1 else old_entry.help_category
                    lockstring = ",".join(lhslist[2:]) if nlist > 2 else old_entry.locks.get()
                    break

        category = category.lower()

        if "edit" in switches:
            # open the line editor to edit the helptext. No = is needed.
            if old_entry:
                topicstr = old_entry.key
                if self.rhs:
                    # we assume append here.
                    old_entry.entrytext += "\n%s" % self.rhs
                helpentry = old_entry
            else:
                helpentry = create.create_help_entry(
                    topicstr,
                    self.rhs if self.rhs is not None else "",
                    category=category,
                    locks=lockstring,
                    aliases=aliases,
                )
            self.caller.db._editing_help = helpentry

            EvEditor(
                self.caller,
                loadfunc=_loadhelp,
                savefunc=_savehelp,
                quitfunc=_quithelp,
                key="topic {}".format(topicstr),
                persistent=True,
            )
            return

        if "append" in switches or "merge" in switches or "extend" in switches:
            # merge/append operations
            if not old_entry:
                self.msg(f"Could not find topic '{topicstr}'. You must give an exact name.")
                return
            if not self.rhs:
                self.msg("You must supply text to append/merge.")
                return
            if "merge" in switches:
                old_entry.entrytext += " " + self.rhs
            else:
                old_entry.entrytext += "\n%s" % self.rhs
            old_entry.aliases.add(aliases)
            self.msg(f"Entry updated:\n{old_entry.entrytext}{aliastxt}")
            return

        if "category" in switches:
            # set the category
            if not old_entry:
                self.msg(f"Could not find topic '{topicstr}'{aliastxt}.")
                return
            if not self.rhs:
                self.msg("You must supply a category.")
                return
            category = self.rhs.lower()
            old_entry.help_category = category
            self.msg(f"Category for entry '{topicstr}'{aliastxt} changed to '{category}'.")
            return

        if "locks" in switches:
            # set the locks
            if not old_entry:
                self.msg(f"Could not find topic '{topicstr}'{aliastxt}.")
                return
            show_locks = not rhslist
            clear_locks = rhslist and not rhslist[0]
            if show_locks:
                self.msg(f"Current locks for entry '{topicstr}'{aliastxt} are: {old_entry.locks}")
                return
            if clear_locks:
                old_entry.locks.clear()
                old_entry.locks.add("read:all()")
                self.msg(f"Locks for entry '{topicstr}'{aliastxt} reset to: read:all()")
                return
            lockstring = ",".join(rhslist)
            # locks.validate() does not throw an exception for things like "read:id(1),read:id(6)"
            # but locks.add() does
            existing_locks = old_entry.locks.all()
            old_entry.locks.clear()
            try:
                old_entry.locks.add(lockstring)
            except LockException as e:
                old_entry.locks.add(existing_locks)
                self.msg(str(e) + " Locks not changed.")
            else:
                self.msg(f"Locks for entry '{topicstr}'{aliastxt} changed to: {lockstring}")
            return

        if "delete" in switches or "del" in switches:
            # delete the help entry
            if not old_entry:
                self.msg(f"Could not find topic '{topicstr}'{aliastxt}.")
                return
            old_entry.delete()
            self.msg(f"Deleted help entry '{topicstr}'{aliastxt}.")
            return

        # at this point it means we want to add a new help entry.
        if not self.rhs:
            self.msg("You must supply a help text to add.")
            return
        if old_entry:
            if "replace" in switches:
                # overwrite old entry
                old_entry.key = topicstr
                old_entry.entrytext = self.rhs
                old_entry.help_category = category
                old_entry.locks.clear()
                old_entry.locks.add(lockstring)
                old_entry.aliases.add(aliases)
                old_entry.save()
                self.msg(f"Overwrote the old topic '{topicstr}'{aliastxt}.")
            else:
                self.msg(
                    f"Topic '{topicstr}'{aliastxt} already exists. Use /edit to open in editor, or "
                    "/replace, /append and /merge to modify it directly."
                )
        else:
            # no old entry. Create a new one.
            new_entry = create.create_help_entry(
                topicstr, self.rhs, category=category, locks=lockstring, aliases=aliases
            )
            if new_entry:
                self.msg(f"Topic '{topicstr}'{aliastxt} was successfully created.")
                if "edit" in switches:
                    # open the line editor to edit the helptext
                    self.caller.db._editing_help = new_entry
                    EvEditor(
                        self.caller,
                        loadfunc=_loadhelp,
                        savefunc=_savehelp,
                        quitfunc=_quithelp,
                        key="topic {}".format(new_entry.key),
                        persistent=True,
                    )
                    return
            else:
                self.msg(f"Error when creating topic '{topicstr}'{aliastxt}! Contact an admin.")

class CmdDataReload(MuxCommand):
    key = "@datareload"
    locks = "cmd:perm(datareload) or perm(Developer)"
    help_category = "data"

    def func(self):
        # Reset the static properties of all abilities to apply any adjustments from code changes
        entities = CombatEntity.objects.all_family()
        for entity in entities:
            for ability in entity.db.abilities:
                ability.at_object_creation()

class CmdTeach(MuxCommand):
    """
            add an ability to a combat entity

            Usage:
              teach <character> = <ability>

            Examples:
               teach lyrik = poison arrow

            Use this to insert an ability into a combat entity's repertoire
            for testing or fixes. Must be in the same room as the target and
            use full names.
            """
    key = "@teach"
    switch_options = ()
    locks = "cmd:perm(teach) or perm(Developer)"
    help_category = "data"

    def func(self):
        if not self.lhs or not self.rhs:
            self.caller.msg("Usage: teach <character> = <ability>")
            return
        name_input = self.lhs
        ability_input = self.rhs

        char = None
        for obj in self.caller.location.contents:
            if obj.key.lower() == name_input.lower() and isinstance(obj, CombatEntity):
                char = obj

        if not char:
            self.caller.msg(f"No character found here matching '{name_input}'.")
            return

        ability = all_abilities.get(ability_input.lower())
        if not ability:
            self.caller.msg(f"No ability found matching '{ability_input}'.")
            return

        instance = create_object(typeclass=ability, key = ability.key, location = char)
        char.db.abilities.append(instance)
        self.caller.location.msg_contents(f"{self.caller.get_display_name()} taught the {instance.get_display_name()} "
                                          f"ability to {char.get_display_name()}.")



class GameDataCmdSet(CmdSet):
    def at_cmdset_creation(self):
        self.add(MyCmdSetHelp)
        self.add(CmdDataReload)
        self.add(CmdTeach)
