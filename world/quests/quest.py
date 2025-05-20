"""
QUEST HOOKS:
    Items
        at_give
            qid
            msg
            next_stage
    Characters
        at_talk
            qid
            spoken_lines
            next_stage
        at_told
            qid
            options
                keywords
                spoken_lines
                next_stage
        at_defeat
            qid
            msg
            next_stage
        at_object_receive
            qid
            spoken_lines
            next_stage
    Rooms
        at_object_receive
            qid
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
