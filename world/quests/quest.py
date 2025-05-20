"""
QUEST HOOKS:
    Items
        at_give
            msg
            next_stage
    Characters
        at_talk
            spoken_lines
            next_stage
        at_told
            options
                keywords
                spoken_lines
                next_stage
        at_defeat
            msg
            next_stage
        at_object_receive
            spoken_lines
            next_stage
    Rooms
        at_object_receive
            msg
            next_stage
"""

from evennia import GLOBAL_SCRIPTS

from typeclasses.scripts.scripts import Script


def all_quests():
    quests = GLOBAL_SCRIPTS.get("All Quests").db.quests
    quests = dict(sorted(quests.items()))
    return quests


class Quest(Script):
    def at_script_creation(self):
        super().at_script_creation()
        self.db.qid = None
        self.db.recommended_level = None
        self.db.desc = ""
        self.db.stages = {}  # Number: desc
