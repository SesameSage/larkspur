from world.quests import quest_hooks, quest

LOCKS = "view:perm(Builder); read:perm(Builder)"

HELP_QUEST_BUILD = {
    "locks": LOCKS,
    "key": "quest building",
    "aliases": ["quest build", "questbuild"],
    "category": "Building",
    "text": quest.__doc__
}
HELP_QUEST_HOOKS = {
    "locks": LOCKS,
    "key": "quest hooks",
    "aliases": ["quest hook", "hook"],
    "category": "Building",
    "text": quest_hooks.__doc__
}