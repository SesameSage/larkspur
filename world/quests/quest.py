from evennia import GLOBAL_SCRIPTS

from typeclasses.scripts.scripts import Script

def all_quests():
    quests = GLOBAL_SCRIPTS.get("All Quests").db.quests
    quests = dict(sorted(quests.items()))
    return quests


def get_quest(qid):
    try:
        return all_quests()[qid]
    except KeyError:
        return None


def get_stage(qid, stage):
    quest_data = get_quest(qid)
    if quest_data is None or stage is None:
        return None
    try:
        return quest_data["stages"][stage]
    except KeyError:
        return None


def quest_desc(qid, stage=None):
    if stage is not None:
        stage_dict = get_stage(qid, stage)
        if stage_dict is None:
            return ""
        else:
            try:
                return stage_dict["desc"]
            except KeyError:
                return ""
    else:
        quest_dict = get_quest(qid)
        if quest_dict is None:
            return ""
        else:
            try:
                return quest_dict["desc"]
            except KeyError:
                quest_dict["desc"] = ""
                return quest_dict["desc"]


class Quest(Script):
    def at_script_creation(self):
        super().at_script_creation()
        self.db.qid = None
        self.db.recommended_level = None
        self.db.desc = ""
        self.db.long_desc = ""
        self.db.stages = {}  # Number: desc
