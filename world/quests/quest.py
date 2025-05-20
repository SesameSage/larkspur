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
            spoken lines
            next_stage
        at_told
            qid
            options
                keywords
                spoken lines
                next_stage
        at_defeat
            qid
            msg
            next_stage
        at_object_receive
            qid
            spoken lines
            next_stage
    Rooms
        at_object_receive
            qid
            msg
            next_stage
"""

from evennia import GLOBAL_SCRIPTS
from evennia.utils.dbserialize import _SaverList

from server import appearance
from typeclasses.scripts.scripts import Script


def all_quests():
    quests = GLOBAL_SCRIPTS.get("All Quests").db.quests
    quests = dict(sorted(quests.items()))
    return quests


def print_quest_hooks(obj, caller):
    for hook_type in obj.db.quest_hooks:
        if len(obj.db.quest_hooks[hook_type]) < 1:
            continue
        caller.msg(f"|w{hook_type} hooks:")
        caller.msg("--------------------------------------")

        for quest_hook in obj.db.quest_hooks[hook_type]:
            try:
                stage = quest_hook["stage"]
                caller.msg(f"   |wQuest #{quest_hook["qid"]}.{stage}")
            except KeyError:
                caller.msg(f"   |wQuest #{quest_hook["qid"]}")

            for hook_attr_key in quest_hook:
                if hook_attr_key == "qid" or hook_attr_key == "stage":
                    continue  # Already listed above
                value = quest_hook[hook_attr_key]

                # at_told options have nested containers
                if hook_attr_key == "options":
                    caller.msg(f"      options:")
                    for i, option in enumerate(value):
                        caller.msg(f"         {i}:")
                        for option_attr_key in option:
                            option_attr_value = option[option_attr_key]
                            if isinstance(option_attr_value, _SaverList):  # Keywords and spoken lines
                                caller.msg(f"            {option_attr_key}:")
                                for val in option_attr_value:
                                    caller.msg(f"               {appearance.say}{val}")
                            else:
                                caller.msg(f"            {option_attr_key}: {option_attr_value}")

                # Spoken lines are contained in a list
                elif hook_attr_key == "spoken lines":
                    caller.msg(f"      {hook_attr_key}:")
                    for line in value:
                        caller.msg(f"         {appearance.say}{line}")

                # All other quest hook attributes without nested containers
                else:  #
                    caller.msg(f"      {hook_attr_key}: {value}")

            caller.msg("---------------------------------")  # After each quest hook


class Quest(Script):
    def at_script_creation(self):
        super().at_script_creation()
        self.db.qid = None
        self.db.recommended_level = None
        self.db.desc = ""
        self.db.stages = {}  # Number: desc
