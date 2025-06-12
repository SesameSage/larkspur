"""
Quests are identified with a quest ID number (QID), and are broken up into stages identified by stage number.
Player characters store their quest progress in a quest_stages dict matching active QIDs to the player's current stage.

A global "All Quests" script contains a dictionary which stores each created quest's QID, level, descriptions, and each
stage's data by number, including descriptions and automatically set references to the hook type, object, and location.
Use the 'questedit' command to view this data.
The 'desc' attribute of quests and stages are the simplest definition shown to players, e.g. quests like "Begin your
journey" or "Help an injured hunter," and stages like "Talk to Attoah," "Pick up the quarterstaff," "Kill 5 cultists",
etc.
The 'long_desc' attribute is akin to the player character's journal/log entry, e.g. "I've come across a hunter on the
road. It looks like he's hurt.", or "I found the relic in the tomb, but it's not what Lorto expected. I should return to
talk to him."

The hook type, object, and location entries are references that are set when a quest hook is created on an object.
Quest hooks are defined and stored in the attributes of the associated object, and are solely responsible for the logic
of quest objectives. Players advance through stages in quests by triggering particular quest hooks while they are at
the associated quest stage. Hooks are triggered by performing actions such as talking to NPCs, defeating enemies, or
giving and getting items.
See 'help quest hooks' for more information.
"""

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


# TODO: Account for multiple objects with hooks per quest stage

def get_hook_object(qid, stage):
    return get_stage(qid, stage)["object"]


def get_hook_data(qid, stage):
    objective_type = get_stage(qid, stage)["objective_type"]
    return get_hook_object(qid, stage).db.quest_hooks[objective_type][qid][stage]


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
