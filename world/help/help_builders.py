from world.quests import quest_hooks

LOCKS = "view:perm(Builder); read:perm(Builder)"

HELP_QUEST_HOOKS = {
    "locks": LOCKS,
    "key": "quest hooks",
    "aliases": ["quest hook", "hook"],
    "category": "Building",
    "text": quest_hooks.__doc__
}