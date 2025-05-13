from collections import defaultdict
from itertools import chain

from evennia import Command
from evennia.commands.default.help import CmdHelp, HelpCategory
from evennia.help.utils import help_search_with_index, parse_entry_for_subcategories
from evennia.utils import inherits_from


class MyCmdHelp(CmdHelp):
    def func(self):
        """
        Run the dynamic help entry creator.
        """
        caller = self.caller
        query, subtopics, cmdset = self.topic, self.subtopics, self.cmdset
        clickable_topics = self.clickable_topics

        if not query:
            # list all available help entries, grouped by category. We want to
            # build dictionaries {category: [topic, topic, ...], ...}

            cmd_help_topics, db_help_topics, file_help_topics = self.collect_topics(
                caller, mode="list"
            )

            # db-topics override file-based ones
            file_db_help_topics = {**file_help_topics, **db_help_topics}

            # group by category (cmds are listed separately)
            cmd_help_by_category = defaultdict(list)
            file_db_help_by_category = defaultdict(list)

            # get a collection of all keys + aliases to be able to strip prefixes like @
            key_and_aliases = set(chain(*(cmd._keyaliases for cmd in cmd_help_topics.values())))

            for key, cmd in cmd_help_topics.items():
                key = self.strip_cmd_prefix(key, key_and_aliases)
                cmd_help_by_category[cmd.help_category].append(key)
            for key, entry in file_db_help_topics.items():
                file_db_help_by_category[entry.help_category].append(key)

            # generate the index and display
            output = self.format_help_index(
                cmd_help_by_category, file_db_help_by_category, click_topics=clickable_topics
            )
            self.msg_help(output)

            return

        # search for a specific entry. We need to check for 'read' access here before
        # building the set of possibilities.
        cmd_help_topics, db_help_topics, file_help_topics = self.collect_topics(
            caller, mode="query"
        )

        # get a collection of all keys + aliases to be able to strip prefixes like @
        key_and_aliases = set(chain(*(cmd._keyaliases for cmd in cmd_help_topics.values())))

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

        # lunr search fields/boosts
        match, suggestions = self.do_search(query, entries)

        if not match:
            # no topic matches found. Only give suggestions.
            help_text = f"There is no help topic matching '{query}'."

            if not suggestions:
                # we don't even have a good suggestion. Run a second search,
                # doing a full-text search in the actual texts of the help
                # entries

                search_fields = [
                    {"field_name": "text", "boost": 1},
                ]

                for match_query in [query, f"{query}*", f"*{query}"]:
                    _, suggestions = help_search_with_index(
                        match_query,
                        entries,
                        suggestion_maxnum=self.suggestion_maxnum,
                        fields=search_fields,
                    )
                    if suggestions:
                        help_text += (
                            "\n... But matches were found within the help "
                            "texts of the suggestions below."
                        )
                        suggestions = [
                            self.strip_cmd_prefix(sugg, key_and_aliases) for sugg in suggestions
                        ]
                        break

            output = self.format_help_entry(
                topic=None,  # this will give a no-match style title
                help_text=help_text,
                suggested=suggestions,
                click_topics=clickable_topics,
            )

            self.msg_help(output)
            return

        if isinstance(match, HelpCategory):
            # no subtopics for categories - these are just lists of topics
            category = match.key
            category_lower = category.lower()
            cmds_in_category = [
                key for key, cmd in cmd_help_topics.items() if category_lower == cmd.help_category
            ]
            topics_in_category = [
                key
                for key, topic in file_db_help_topics.items()
                if category_lower == topic.help_category
            ]
            output = self.format_help_index(
                {category: cmds_in_category},
                {category: topics_in_category},
                title_lone_category=True,
                click_topics=clickable_topics,
            )
            self.msg_help(output)
            return

        if inherits_from(match, "evennia.commands.command.Command"):
            # a command match
            topic = match.key
            help_text = match.get_help(caller, cmdset)
            aliases = match.aliases
            suggested = suggestions[1:]
        else:
            # a database (or file-help) match
            topic = match.key
            help_text = match.entrytext
            aliases = match.aliases if isinstance(match.aliases, list) else match.aliases.all()
            suggested = suggestions[1:]

        # parse for subtopics. The subtopic_map is a dict with the current topic/subtopic
        # text is stored under a `None` key and all other keys are subtopic titles pointing
        # to nested dicts.

        subtopic_map = parse_entry_for_subcategories(help_text)
        help_text = subtopic_map[None]
        subtopic_index = [subtopic for subtopic in subtopic_map if subtopic is not None]

        if subtopics:
            # if we asked for subtopics, parse the found topic_text to see if any match.
            # the subtopics is a list describing the path through the subtopic_map.

            for subtopic_query in subtopics:
                if subtopic_query not in subtopic_map:
                    # exact match failed. Try startswith-match
                    fuzzy_match = False
                    for key in subtopic_map:
                        if key and key.startswith(subtopic_query):
                            subtopic_query = key
                            fuzzy_match = True
                            break

                    if not fuzzy_match:
                        # startswith failed - try an 'in' match
                        for key in subtopic_map:
                            if key and subtopic_query in key:
                                subtopic_query = key
                                fuzzy_match = True
                                break

                    if not fuzzy_match:
                        # no match found - give up
                        checked_topic = topic + f"{self.subtopic_separator_char}{subtopic_query}"
                        output = self.format_help_entry(
                            topic=topic,
                            help_text=f"No help entry found for '{checked_topic}'",
                            subtopics=subtopic_index,
                            click_topics=clickable_topics,
                        )
                        self.msg_help(output)
                        return

                # if we get here we have an exact or fuzzy match

                subtopic_map = subtopic_map.pop(subtopic_query)
                subtopic_index = [subtopic for subtopic in subtopic_map if subtopic is not None]
                # keep stepping down into the tree, append path to show position
                topic = topic + f"{self.subtopic_separator_char}{subtopic_query}"

            # we reached the bottom of the topic tree
            help_text = subtopic_map[None]

        topic = self.strip_cmd_prefix(topic, key_and_aliases)
        if subtopics:
            aliases = None
        else:
            aliases = [self.strip_cmd_prefix(alias, key_and_aliases) for alias in aliases]
        suggested = [self.strip_cmd_prefix(sugg, key_and_aliases) for sugg in suggested]

        output = self.format_help_entry(
            topic=topic,
            help_text=help_text,
            aliases=aliases,
            subtopics=subtopic_index,
            suggested=suggested,
            click_topics=clickable_topics,
        )
        self.msg_help(output)

class CmdMoreInfo(Command):
    """
        toggle seeing real-time combat calculations

        Usage:
          moreinfo

        This command changes the moreinfo preference for this character.
        Setting moreinfo to True displays an array of faded messages
        on the status of calculations in combat.
        """
    key = "moreinfo"
    help_category = "appearance"

    def func(self):
        self.caller.attributes.get("prefs", category="ooc")["more_info"] = \
            not self.caller.attributes.get("prefs", category="ooc")["more_info"]
        self.caller.print_ambient(
            f"MoreInfo set to {self.caller.attributes.get("prefs", category="ooc")["more_info"]}.")


class CmdHere(Command):
    """
        see info on your location

        Usage:
          here

        The "here" command shows your current room's area, locality,
        zone, and region.
        """
    key = "here"
    help_category = "navigation"

    def func(self):
        room = self.caller.location
        area = room.db.area.key if room.db.area else "None"
        locality = room.locality().key if room.locality() else "None"
        zone = room.zone().key if room.zone() else "None"
        region = room.region().key if room.region() else "None"

        self.caller.msg(f"|wRoom:|n {room.get_display_name()}\n"
                        f"|wArea:|n {area}\n"
                        f"|wLocality:|n {locality}\n"
                        f"|wZone:|n {zone}\n"
                        f"|wRegion:|n {region}\n")
