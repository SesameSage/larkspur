from evennia.utils.dbserialize import _SaverList

from server import appearance
from world.quests.quest import all_quests, quest_desc


def get_hook_type(obj, qid, stage):
    quest_hooks = obj.db.quest_hooks
    for hook_type in quest_hooks:
        for hook_qid in quest_hooks[hook_type]:
            if hook_qid == qid:
                for hook_stage in quest_hooks[hook_type][qid]:
                    if hook_stage == stage:
                        return hook_type


def print_quest_hooks(obj, caller):
    for hook_type in obj.db.quest_hooks:
        hooks = obj.db.quest_hooks[hook_type]
        if len(hooks) < 1:
            continue
        caller.msg(f"|w{hook_type} hooks:")
        caller.msg("--------------------------------------")

        for qid in hooks:
            desc = quest_desc(qid)
            caller.msg(f"|wQuest #{qid} - {desc}")
            for stage in hooks[qid]:
                quest_hook = hooks[qid][stage]
                desc = quest_desc(qid, stage)
                caller.msg(f"   Stage {stage}: ({desc})")
                for hook_attr_key in quest_hook:
                    if hook_attr_key == "qid" or hook_attr_key == "stage":
                        continue  # Already listed above
                    value = quest_hook[hook_attr_key]

                    # at_told options have nested containers
                    if hook_attr_key == "options":
                        caller.msg(f"      options:")
                        for i, option in enumerate(value):
                            caller.msg(f"            {i}:")
                            for option_attr_key in option:
                                option_attr_value = option[option_attr_key]

                                # Keywords and spoken lines
                                if isinstance(option_attr_value, _SaverList):
                                    caller.msg(f"               {option_attr_key}:")
                                    for val in option_attr_value:
                                        caller.msg(f"                  {appearance.say}{val}")

                                # Get description of next stage
                                elif option_attr_key == "next_stage":
                                    desc = quest_desc(qid, option_attr_value)
                                    caller.msg(f"                  {option_attr_key}: {option_attr_value} - {desc}")

                                else:
                                    caller.msg(f"               {option_attr_key}: {option_attr_value}")

                    # Spoken lines are contained in a list
                    elif hook_attr_key == "spoken_lines":
                        caller.msg(f"      {hook_attr_key}:")
                        for line in value:
                            caller.msg(f"         {appearance.say}{line}")

                    # Get description of next stage
                    elif hook_attr_key == "next_stage":
                        desc = quest_desc(qid, value)
                        caller.msg(f"      {hook_attr_key}: {value} - {desc}")

                    # All other quest hook attributes
                    else:  #
                        caller.msg(f"      {hook_attr_key}: {value}")

                caller.msg("---------------------------------")  # After each quest hook
