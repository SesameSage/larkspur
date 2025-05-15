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
