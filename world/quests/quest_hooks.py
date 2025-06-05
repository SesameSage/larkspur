"""
Quest hooks tie quest stages/objectives to objects in the world and particular actions that can be performed on them.

The logic and progression of quests comes entirely from the triggering of quest hooks by players - performing the
specified action on the specified object while the player is at the associated quest stage.

For example:
    - If an at_talk hook is attached to the character Attoah for stage 12.9 (QID 12, stage 9), and the player
        enters "talk Attoah":
        - If the player hasn't started quest 12, or their current objective for quest 12 is a stage other than stage 9,
            the hook is not triggered.
        - If the player has stage 9 as their current objective for quest 12, Attoah will speak the dialogue lines in
            the hook's spoken_lines one by one, and then the player's current objective for quest 12 will be stage 9's
            next_stage, most likely stage 10.

    - If an at_get hook is attached to a relic item for objective 17.0:
        - Players default to stage 0 of every quest. Hooks at stage 0 represent an action any player will be able to
            trigger, as long as they have not yet started this quest.
        - When a player picks up the relic, quest 17 will start for the player (current stage becomes 1).

    - If an at_told hook is attached to Attoah for stage 8.1:
        - If the player has not yet started the quest (at stage 0), "tell Attoah" has no effect.
        - If the player is at this quest stage:
            - Each dialogue option in the hook data has its own keywords, spoken_lines, and next_stage.
            - If the player uses all of an option's keywords in a "tell" message to Attoah, that option's spoken_lines
                are said, and the player advanced to that option's next_stage.

Structure of quest hooks:
    {hook_type: {QID: {stage: {hook_data}}}}

    obj.db.quest_hooks = {hook_type: {}, hook_type: {}}
        hook_type: {qid: {}, qid: {}}
            qid: {stage: {}, stage: {}}
                stage: {desc: "",
                        objective_type: "",
                        object: obj,
                        location: ""}

Properties of quest hooks by object type and hook type:
    Items
        at_get
            msg
            next_stage
        at_give
            msg
            getter
            next_stage
    Entities
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
import collections

from evennia.utils import inherits_from
from evennia.utils.dbserialize import _SaverList
from evennia.utils.evtable import EvTable

from server import appearance
from world.quests.quest import get_stage, quest_desc


def get_hook_type(obj, qid, stage):
    """Given an object with quest hooks, returns the hook/objective type assigned to the given qid and stage."""
    quest_hooks = obj.db.quest_hooks
    for hook_type in quest_hooks:
        for hook_qid in quest_hooks[hook_type]:
            if hook_qid == qid:
                for hook_stage in quest_hooks[hook_type][qid]:
                    if hook_stage == stage:
                        return hook_type


def location_string(qid, stage, objective_type=None, obj=None):
    """Displays the location of the quest stage, with specificity determined by the objective type and object."""
    stage = get_stage(qid, stage)
    objective_type = objective_type or stage.get("objective_type", "")
    obj = obj or stage.get("object", None)

    if objective_type == "at_give":
        obj = stage.get("getter", None)
    elif objective_type == "kill_counter":
        return ""

    if not obj:
        return ""

    area_string = f"{obj.location.db.area.key}, {obj.location.locality().key}, {obj.location.zone().key}"
    if inherits_from(obj, "typeclasses.living.living_entities.LivingEntity") and objective_type != "at_defeat":
        return f"{obj.location.key}, " + area_string
    else:
        return area_string


def print_all_hooks(obj, caller):
    """Shows the QID and stage # of all quest hooks attached to the given object, sorted by quest and stage."""
    hooks = {}
    for hook_type in obj.db.quest_hooks:
        hooks_of_type = obj.db.quest_hooks[hook_type]

        for qid in hooks_of_type:
            quest_dict = {}
            try:
                hooks[qid]
            except KeyError:
                hooks[qid] = {}
            for stage in hooks_of_type[qid]:
                quest_hook = hooks_of_type[qid][stage]
                quest_dict[stage] = quest_hook, hook_type

            quest_dict = collections.OrderedDict(sorted(quest_dict.items()))
            hooks[qid] = quest_dict

    hooks = collections.OrderedDict(sorted(hooks.items()))

    caller.msg(f"{obj.get_display_name()} has the following quest hooks:")
    table = EvTable("Quest", "Stage", "Hook Type", "Description", pretty_corners=True)
    for qid in hooks:
        table.add_row(f"|wQuest #{qid}", "", "", "|w" + quest_desc(qid))
        alternate_color = True
        for stage in hooks[qid]:
            alternate_color = not alternate_color
            quest_hook, hook_type = hooks[qid][stage]
            color = appearance.table_alt if alternate_color else ""
            table.add_row("", color + f"Stage #{stage}", color + hook_type, color + quest_desc(qid, stage))
        table.add_row()
    caller.msg(table)


def print_quest_hook(caller, qid, stage, quest_hook):
    q_desc = quest_desc(qid)
    stage_desc = quest_desc(qid, stage)
    caller.msg(f"|wQuest #{qid} - {q_desc}")
    caller.msg(f"   Stage {stage}: ({stage_desc})")
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
                        caller.msg(f"               {option_attr_key}: {option_attr_value} - {desc}")

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
