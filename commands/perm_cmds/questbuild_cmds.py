import evennia
from evennia.commands.cmdset import CmdSet
from evennia.commands.default.muxcommand import MuxCommand
from evennia.utils import inherits_from
from evennia.utils.evtable import EvTable

from server import appearance
from world.quests.quest import all_quests, quest_desc
from world.quests.quest_hooks import print_quest_hooks, get_hook_type


class CmdQuestEdit(MuxCommand):
    """
        show or edit player-facing quest data

        Usage:
          questedit                      (all quests)
          qe <QID>                       (all stages of this quest)
          qe/level <QID> = <level>       (set quest level)
          qe/desc <QID> = <quest desc>   (set quest desc)
          qe/desc <QID>.<stage> = <desc> (set stage desc)

        Examples:
           qe 12
           qe/level 8 = 2
           qe/desc 0 = Start your journey
           qe/desc 0.0 = Talk to the trainer

        ('qe'): Show all quests by quest ID, recommended level, and quest description.

        ('qe <QID>'): Show all stages of this quest, their descriptions, objective types, and object the quest hook
        is attached to.

        ('qe/desc <QID>'): Edit the description of an entire quest

        ('qe/level <QID>'): Edit the recommended level for a quest

        ('qe/desc <QID>.<stage>'): Edit the description of a specific quest objective/stage
        """
    key = "questedit"
    aliases = ("qe",)
    switch_options = ("desc", "level")
    locks = "cmd:perm(questedit) or perm(Builder)"
    help_category = "building"

    def func(self):
        quests = all_quests()
        # If no args, display all quests
        if not self.lhs:
            table = EvTable("QID", "Level", "Description")
            for qid in quests:
                quest = quests[qid]
                level = quest.get("recommended_level", "")
                desc = quest_desc(qid)
                table.add_row(qid, level, desc)
            self.caller.msg(table)
            return

        # If a quest is specified
        else:
            # Parse QID and stage if given
            try:
                num_input = self.lhs.split(".")
                qid = int(num_input[0])
                stage = None
                if len(num_input) > 1:
                    stage = int(num_input[1])
            except ValueError:
                self.caller.msg(
                    f"Couldn't get integers from {self.lhs} (Usage: {appearance.cmd}questedit <qid>[.<stage>])")
                return

            # Display stages of this quest if no edit is being made
            if not self.rhs:
                quest = quests[qid]
                self.caller.msg(f"Quest #{qid}: {quest_desc(qid)}")
                table = EvTable("Stages:", "Decription", "Objective", "Object")
                stages = quest["stages"]
                for stage_num in stages:
                    stage = stages[stage_num]
                    stage_desc = quest_desc(qid, stage_num)
                    try:
                        obj = stage["object"]
                    except KeyError:
                        obj = stage["target_type"]
                    table.add_row(stage_num, stage_desc, stage["objective_type"], obj)
                self.caller.msg(table)
                return

            # If making an edit / setting a value
            else:
                # Default to empty quest info dict if this is the first data on this QID
                try:
                    evennia.GLOBAL_SCRIPTS.get("All Quests").db.quests[qid]
                except KeyError:
                    evennia.GLOBAL_SCRIPTS.get("All Quests").db.quests[qid] = \
                        {"desc": "", "recommended_level": None, "stages": {}}

                if "desc" in self.switches:
                    if stage is None:  # Set description for entire quest
                        evennia.GLOBAL_SCRIPTS.get("All Quests").db.quests[qid]["desc"] = self.rhs
                    else:  # Set description for quest stage
                        # Ensure quest data has the "stages" dict
                        try:
                            evennia.GLOBAL_SCRIPTS.get("All Quests").db.quests[qid]["stages"]
                        except KeyError:
                            evennia.GLOBAL_SCRIPTS.get("All Quests").db.quests[qid]["stages"] = {}
                        # Ensure the stages data includes this stage
                        try:
                            evennia.GLOBAL_SCRIPTS.get("All Quests").db.quests[qid]["stages"][stage]["desc"] = self.rhs
                        except KeyError:
                            evennia.GLOBAL_SCRIPTS.get("All Quests").db.quests[qid]["stages"][stage] = {
                                "desc": self.rhs,
                                "objective_type": ""}
                        return

                elif "level" in self.switches:
                    # Parse level value
                    try:
                        level = int(self.rhs)
                    except ValueError:
                        self.caller.msg("Couldn't get an integer level from " + self.rhs)

                    # Default to empty quest info dict if this is the first data on this QID
                    try:
                        evennia.GLOBAL_SCRIPTS.get("All Quests").db.quests[qid]
                    except KeyError:
                        evennia.GLOBAL_SCRIPTS.get("All Quests").db.quests[qid] = \
                            {"desc": "", "recommended_level": None, "stages": {}}

                    # Set recommended level in quest data
                    evennia.GLOBAL_SCRIPTS.get("All Quests").db.quests[qid]["recommended_level"] = level
                    return


class CmdQuestHook(MuxCommand):
    # TODO: help quest hooks
    """
        view, add, edit, and remove quest hooks from objects

        Usage:
            questhook <object>
            qh/add <object> = <QID>.<stage>:<hook_type>
            qh/remove <object> = <QID>.<stage>
            qh/edit <object> = <QID>.<stage>

        Examples:
           questhook attoah
           qh/add package = 4.0:at_give
           qh/remove package = 4.0
           qh/edit attoah = 12.2

        Available hook types for different object types in 'help quest hooks'.
        Editing a quest hook prompts which attribute to edit and what value to give.
        Adding a quest hook automatically sets attributes on the quest stage in the all_quests container.
        """
    key = "questhook"
    aliases = ("qh",)
    switch_options = ("add", "remove", "edit")
    locks = "cmd:perm(questhook) or perm(Builder)"
    help_category = "building"

    def func(self):
        if not self.lhs:
            self.caller.msg(f"Must supply an object e.g. {appearance.cmd}questhook/<switch> <object> = ...")
            return
        # Arg left of "=" is object quest hook should be attached to
        obj_input = self.lhs
        obj = self.caller.search(obj_input)
        if not obj:
            return
        elif not obj.db.quest_hooks:
            self.caller.msg(f"{obj.name} doesn't handle quest hooks!")
            return

        # Creating or altering a quest hook; parse right of = if needed
        rhs_needed = True
        if "remove" in self.switches or "edit" in self.switches:
            rhs_needed = False
        if self.switches:
            error_msgs = [f"Need a QID and arg! Usage: ", f"{appearance.cmd}questhook/add <object> = <qid>:<hook type>",
                          f"{appearance.cmd}questhook/msg <object> = <qid>:<stage>"]
            if not self.rhs and rhs_needed:
                for msg in error_msgs:
                    self.caller.msg(msg)
                return
            rhs_args = self.rhs.split(":")
            numbers = rhs_args[0].split(".")
            try:
                qid = int(numbers[0])
                stage = int(numbers[1])
            except ValueError:
                self.caller.msg(f"Couldn't parse {numbers[0]}.{numbers[1]} as a QID.stage integer pair")
                return
            if len(rhs_args) < 2 and rhs_needed:
                for msg in error_msgs:
                    self.caller.msg(msg)
                return

        # No switch statements: display quest hooks
        else:
            print_quest_hooks(obj, self.caller)
            return

        if "add" in self.switches:  # Right of = is QID:hook i.e. = 3:at_give
            # Make sure this object handles hooks of this type
            objective_type = rhs_args[1]
            if objective_type not in obj.db.quest_hooks:
                self.caller.msg(f"{obj.key} doesn't handle quest hooks of that type. "
                                f"Handles: {[typ for typ in obj.db.quest_hooks]}")
                return

            # Create the data for the quest hook on the object
            obj.db.quest_hooks[objective_type][qid] = {}
            obj.db.quest_hooks[objective_type][qid][stage] = {}

            # Add hook info to quest data
            quests = all_quests()
            try:
                quests[qid]
            except KeyError:
                quests[qid] = {"stages": {}}
            try:
                quests[qid]["stages"][stage] = {}
                quests[qid]["stages"][stage]["objective_type"] = objective_type
                quests[qid]["stages"][stage]["object"] = obj
            except KeyError:
                quests[qid]["stages"][stage] = {"objective_type": objective_type, "object": obj}

        elif "remove" in self.switches:
            objective_type = get_hook_type(obj, qid, stage)
            del obj.db.quest_hooks[objective_type][qid][stage]
            del obj.db.quest_hooks[objective_type][qid]
            quests = evennia.GLOBAL_SCRIPTS.get("All Quests").db.quests
            del quests[qid]["stages"][stage]

        elif "edit" in self.switches:
            # Show the proper attributes editable according to objective/hook type
            hook_type = get_hook_type(obj, qid, stage)
            options = []
            if (hook_type in ["at_give", "at_defeat"] or
                    inherits_from(obj, "world.locations.rooms.Room") and hook_type == "at_object_receive"):
                options.append("msg")
            if (hook_type == "at_talk" or
                    inherits_from(obj, "typeclasses.living.living_entities.LivingEntity")
                    and hook_type == "at_object_receive"):
                options.append("spoken_lines")
            if hook_type == "at_told":
                options.append("options")
            if hook_type != "at_told":
                options.append("next_stage")

            # Choose aspect of hook to edit
            inpt = yield f"Select quest hook attribute to edit: ({str(options)})"
            # Set value
            match inpt:
                case "msg":
                    msg = yield "Enter message:"
                    obj.db.quest_hooks[hook_type][qid][stage]["msg"] = msg

                case "next_stage":
                    next_stage = yield "Enter next stage:"
                    obj.db.quest_hooks[hook_type][qid][stage]["next_stage"] = next_stage

                case "spoken_lines":
                    line_inpt = yield "Write lines separated by '/':"
                    lines = line_inpt.split("/")
                    lines = [line.strip() for line in lines]
                    obj.db.quest_hooks[hook_type][qid][stage]["spoken_lines"] = lines

                # Dialogue options in at_told hooks
                case "options":
                    # Option index
                    opt_num = yield "Option number to edit (0 indexed):"
                    try:
                        opt_num = int(opt_num)
                    except ValueError:
                        self.caller.msg("Couldn't get an integer from " + opt_num)
                        return

                    # Option data
                    try:
                        opt_dict = obj.db.quest_hooks[hook_type][qid][stage]["options"][opt_num]
                    except KeyError:
                        opt_dict = {"keywords": [], "spoken_lines": [], "next_stage": None}

                    # Choose attribute of dialogue option to edit
                    attr = yield "Edit keywords, spoken_lines, or next_stage?:"
                    # Set value
                    match attr:
                        case "keywords":
                            keywords = yield "Enter keywords separated by comma:"
                            words = keywords.split(",")
                            words = [word.strip() for word in words]
                            opt_dict["keywords"] = words

                        case "spoken_lines":
                            line_inpt = yield "Write lines separated by '/':"
                            lines = line_inpt.split("/")
                            lines = [line.strip() for line in lines]
                            opt_dict["spoken_lines"] = lines

                        case "next_stage":
                            next_stage = yield "Enter next stage:"
                            opt_dict["next_stage"] = next_stage

                        case _:
                            self.caller.msg("No valid option found for " + attr)
                            return

                    # Save option data for this dialogue option to the quest hook data
                    try:
                        obj.db.quest_hooks[hook_type][qid][stage]["options"][opt_num] = opt_dict
                    except KeyError:
                        obj.db.quest_hooks[hook_type][qid][stage]["options"] = []
                        obj.db.quest_hooks[hook_type][qid][stage]["options"][opt_num] = opt_dict

                case _:
                    self.caller.msg("No valid option found for " + inpt)


class CmdKillCounter(MuxCommand):
    """
        tie a quest stage to a kill counter objective

        Usage:
            killcounter <QID>.<stage>:<next_stage> = <num_to_kill> <path.to.class>

        Examples:
           kc 0.2:3 = 5 typeclasses.living.enemies.Enemy

        Generates an objective to kill the specified number of the specified type of enemy, and set it as the
        stage objective for the given quest stage.
        Use questedit/desc <QID>.<stage> = <desc> to set the stage/objective's description.
        """
    key = "killcounter"
    aliases = ("kc",)
    locks = "cmd:perm(questhook) or perm(Builder)"
    help_category = "building"

    def func(self):
        usage = f"Usage: {appearance.cmd}killcounter <QID>.<stage>:<next_stage> = <num_to_kill> <path.to.class>"

        # Parse lhs as QID.stage:next_stage =
        try:
            numbers = self.lhs.split(":")
            quest_nums = numbers[0].split(".")
            next_stage = int(numbers[1])
            qid = int(quest_nums[0])
            stage = int(quest_nums[1])
        except ValueError:
            self.caller.msg(f"Couldn't parse '{self.lhs}' as a <QID>.<stage>:<next_stage> integer sequence")
            return
        except IndexError:
            self.caller.msg(usage)
            return

        # Parse rhs as = <number> <path.to.type>
        try:
            rhs = self.rhs.split()
            num_to_kill = int(rhs[0])
            path_to_type = rhs[1]
        except ValueError:
            self.caller.msg(usage)
            return
        except IndexError:
            self.caller.msg(usage)
            return

        # Get quest and stage data
        try:
            quest_dict = all_quests()[qid]
        except KeyError:
            quest_dict = {"desc": "", "stages": {}}
            all_quests()[qid] = quest_dict
        try:
            stage_dict = quest_dict["stages"][stage]
        except KeyError:
            stage_dict = {"desc": ""}

        # Set relevant stage data
        stage_dict["objective_type"] = "kill_counter"
        stage_dict["target_type"] = path_to_type
        stage_dict["kill_num"] = num_to_kill
        stage_dict["next_stage"] = next_stage

        # Reflect changed data in all_quests container
        all_quests()[qid]["stages"][stage] = stage_dict


class QuestBuildCmdSet(CmdSet):
    def at_cmdset_creation(self):
        self.add(CmdQuestEdit)
        self.add(CmdQuestHook)
        self.add(CmdKillCounter)
