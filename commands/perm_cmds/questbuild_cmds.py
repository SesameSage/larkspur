import evennia
from evennia.commands.cmdset import CmdSet
from evennia.commands.default.muxcommand import MuxCommand
from evennia.utils import inherits_from
from evennia.utils.evtable import EvTable

from server import appearance
from world.quests.quest import all_quests, quest_desc, get_quest, get_stage
from world.quests.quest_hooks import print_all_hooks, get_hook_type, location_string, print_quest_hook


class CmdQuestEdit(MuxCommand):
    """
        show or edit player-facing quest data

        Usage:
          questedit                      (all quests)
          qe <QID>                       (all stages of this quest)
          qe/level <QID> = <level>       (set quest level)
          qe/desc <QID> = <quest desc>   (set quest desc)
          qe/desc <QID>.<stage> = <desc> (set stage desc)
          qe/long <QID> = <quest long_desc>   (set quest long_desc)
          qe/long <QID>.<stage> = <long_desc> (set stage long_desc)


        Examples:
           qe 12
           qe/level 8 = 2
           qe/desc 0 = Start your journey
           qe/desc 0.0 = Talk to the trainer
           qe/long 16.4 = I've found the relic in the tomb. I should return to Lorto.

        ('qe'): Show all quests by quest ID, recommended level, and quest description.

        ('qe <QID>'): Show all stages of this quest, their descriptions, objective types, and object the quest hook
        is attached to.

        ('qe/desc <QID>'): Edit the description of an entire quest

        ('qe/level <QID>'): Edit the recommended level for a quest

        ('qe/desc <QID>.<stage>'): Edit the description of a specific quest objective/stage
        """
    key = "questedit"
    aliases = ("qe",)
    switch_options = ("level", "desc", "long")
    locks = "cmd:perm(questedit) or perm(Builder)"
    help_category = "building"

    def func(self):
        quests = all_quests()
        # If no args, display all quests
        if not self.lhs:
            table = EvTable("QID", "Level", "Description")
            alternate_color = True
            for qid in quests:
                alternate_color = not alternate_color
                color = appearance.table_alt if alternate_color else ""
                quest = quests[qid]
                level = quest.get("recommended_level", "")
                desc = quest_desc(qid)
                table.add_row(color + str(qid), color + str(level), color + desc)
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
                try:
                    self.caller.msg(quest["long_desc"])
                except KeyError:
                    pass
                table = EvTable("#", "Decription", "Objective", "Object", "Location", "Long")
                stages = quest["stages"]
                alternate_color = True
                for stage_num in stages:
                    stage = stages[stage_num]
                    stage_desc = quest_desc(qid, stage_num)
                    try:
                        obj = stage["object"]
                    except KeyError:
                        try:
                            obj = stage["target_type"]
                        except KeyError:
                            obj = ""
                    try:
                        long = stage["long_desc"]
                        if len(long) > 35:
                            long = long[:35] + "..."
                    except KeyError:
                        long = ""
                    location = stage.get("location", "")
                    alternate_color = not alternate_color
                    color = appearance.table_alt if alternate_color else ""
                    table.add_row(color + str(stage_num), color + stage_desc, color + stage["objective_type"],
                                  color + obj.key, color + location, color + long)
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
                        self.caller.msg(f"Quest #{qid} short description set to '{self.rhs}'")
                    else:  # Set description for quest stage
                        # Ensure quest data has the "stages" dict
                        try:
                            evennia.GLOBAL_SCRIPTS.get("All Quests").db.quests[qid]["stages"]
                        except KeyError:
                            evennia.GLOBAL_SCRIPTS.get("All Quests").db.quests[qid]["stages"] = {}
                        # Ensure the stages data includes this stage
                        try:
                            evennia.GLOBAL_SCRIPTS.get("All Quests").db.quests[qid]["stages"][stage]["desc"] = self.rhs
                            self.caller.msg(f"Stage {qid}.{stage} short description set to '{self.rhs}'")
                        except KeyError:
                            evennia.GLOBAL_SCRIPTS.get("All Quests").db.quests[qid]["stages"][stage] = {
                                "desc": self.rhs,
                                "objective_type": ""}
                            self.caller.msg(f"Stage {qid}.{stage} short description set to '{self.rhs}'")
                        return

                elif "long" in self.switches:
                    if stage is None:  # Set long_desc for entire quest
                        evennia.GLOBAL_SCRIPTS.get("All Quests").db.quests[qid]["long_desc"] = self.rhs
                        self.caller.msg(f"Quest #{qid} long description set to '{self.rhs}'")
                    else:  # Set long_desc for quest stage
                        # Ensure quest data has the "stages" dict
                        try:
                            evennia.GLOBAL_SCRIPTS.get("All Quests").db.quests[qid]["stages"]
                        except KeyError:
                            evennia.GLOBAL_SCRIPTS.get("All Quests").db.quests[qid]["stages"] = {}
                        # Ensure the stages data includes this stage
                        try:
                            evennia.GLOBAL_SCRIPTS.get("All Quests").db.quests[qid]["stages"][stage]["long_desc"] = (
                                self.rhs)
                            self.caller.msg(f"Stage {qid}.{stage} long description set to '{self.rhs}'")
                        except KeyError:
                            evennia.GLOBAL_SCRIPTS.get("All Quests").db.quests[qid]["stages"][stage] = {
                                "desc": "",
                                "objective_type": "",
                                "long_desc": self.rhs}
                            self.caller.msg(f"Stage {qid}.{stage} long description set to '{self.rhs}'")
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
                    self.caller.msg(f"Quest #{qid} recommended level set to {level}.")
                    return


class CmdQuestHook(MuxCommand):
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

        def parse_lhs():
            """Get the object to attach the hook to from the argument left of the = sign in the entered command line."""
            if not self.lhs:
                self.caller.msg(f"Must supply an object e.g. {appearance.cmd}questhook/<switch> <object> = ...")
                return
            obj_input = self.lhs
            obj = self.caller.search(obj_input)
            if not obj:
                return
            elif not obj.db.quest_hooks:
                self.caller.msg(f"{obj.name} doesn't handle quest hooks!")
                return
            return obj

        def parse_rhs():
            """Get the QID, stage, and hook type (if adding a new hook) from the args right of the = sign."""
            error_msgs = [f"Need a QID and arg! Usage: ", f"{appearance.cmd}questhook/add <object> = "
                                                          f"<qid>.<stage>:<hook type>",
                          f"{appearance.cmd}questhook/edit <object> = <qid>.<stage>",
                          f"{appearance.cmd}questhook/remove <object> = <qid>.<stage>"]

            # All switch options require specifying stage right of =
            if self.switches and not self.rhs:
                for error_msg in error_msgs:
                    self.caller.msg(error_msg)
                return

            # Attempt to parse
            rhs_args = self.rhs.split(":")  # Separates numbers from hook type if adding a new hook
            numbers = rhs_args[0].split(".")  # Separates QID from stage
            try:
                qid = int(numbers[0])
                stage = int(numbers[1])
            except (ValueError, IndexError):
                self.caller.msg(f"Couldn't parse {self.rhs} as a QID.stage integer pair")
                return
            # Not enough values
            if len(rhs_args) < 2 and len(numbers) < 2:
                for msg in error_msgs:
                    self.caller.msg(msg)
                return
            return qid, stage, rhs_args

        def add_hook():
            # Make sure this object handles hooks of this type
            objective_type = rhs_args[1]  # Right of = is QID:hook i.e. = 3:at_give
            if objective_type not in obj.db.quest_hooks:
                self.caller.msg(f"{obj.key} doesn't handle quest hooks of that type. "
                                f"Handles: {[typ for typ in obj.db.quest_hooks]}")
                return

            # Create the data for the quest hook on the object
            try:
                obj.db.quest_hooks[objective_type][qid][stage] = {}
                self.caller.msg(f"Added {objective_type} hook data to {obj.key} for stage {qid}.{stage}")
            except KeyError:
                obj.db.quest_hooks[objective_type][qid] = {}
                obj.db.quest_hooks[objective_type][qid][stage] = {}
                self.caller.msg(f"Added {objective_type} hook data to {obj.key} for stage {qid}.{stage}")

            # Auto-set next_stage
            if objective_type != "at_told":
                stage_str = f"{qid}.{stage + 1}"
                obj.db.quest_hooks[objective_type][qid][stage]["next_stage"] = stage_str
                self.caller.msg(f"Next stage auto-set to {qid}.{stage} - "
                                f"{appearance.cmd}qh/edit {obj.key} = {qid}.{stage}|n to change")

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
                quests[qid]["stages"][stage]["location"] = location_string(qid, stage,
                                                                           objective_type=objective_type, obj=obj)
                self.caller.msg("Attributes auto-set in global quest data.")
            except KeyError:
                quests[qid]["stages"][stage] = {"objective_type": objective_type, "object": obj}
                quests[qid]["stages"][stage]["location"] = location_string(qid, stage)
                self.caller.msg("Attributes auto-set in global quest data.")

            evennia.GLOBAL_SCRIPTS.get("All Quests").db.quests = quests

        def valiate_next_stage(stage_input):
            if stage_input != "None":
                numbers = stage_input.split(".")
                if len(numbers) != 2:
                    self.caller.msg("Next stage must be 'None' or an integer pair formatted as "
                                    "QID.Stage")
                    return False
                for number in numbers:
                    try:
                        int(number)
                    except ValueError:
                        self.caller.msg(f"Couldn't parse '{stage_input}' as a pair of integers.")
                        return False
            return True

        # Arg left of "=" is object quest hook should be attached to
        obj = parse_lhs()
        if not obj:
            return

        # If creating or altering a hook, or specifying a stage to display, parse right of =
        if self.switches or self.rhs:
            rhs_values = parse_rhs()
            if not rhs_values:
                return
            qid, stage, rhs_args = rhs_values

            # If stage given but no switches given, display this quest hook
            if not self.switches:
                if qid is None or stage is None:
                    print_all_hooks(obj, self.caller)
                    return
                print_quest_hook(self.caller, qid, stage,
                                 obj.db.quest_hooks[get_hook_type(obj, qid, stage)][qid][stage])
                return

        # No switch statements or QID/stage args = display all quest hooks
        else:
            print_all_hooks(obj, self.caller)
            return

        if "add" in self.switches:
            add_hook()

        elif "remove" in self.switches:
            objective_type = get_hook_type(obj, qid, stage)
            del obj.db.quest_hooks[objective_type][qid][stage]
            del obj.db.quest_hooks[objective_type][qid]
            quests = evennia.GLOBAL_SCRIPTS.get("All Quests").db.quests
            del quests[qid]["stages"][stage]
            self.caller.msg(f"Stage {qid}.{stage} {objective_type} hook on {obj.key} removed.")

        elif "edit" in self.switches:
            # Show the proper attributes editable according to objective/hook type
            hook_type = get_hook_type(obj, qid, stage)
            options = []
            if (hook_type in ["at_give", "at_defeat", "at_get"] or
                    inherits_from(obj, "world.locations.rooms.Room") and hook_type == "at_object_receive"):
                options.append("msg")
            if (hook_type == "at_talk" or
                    inherits_from(obj, "typeclasses.living.living_entities.LivingEntity")
                    and hook_type == "at_object_receive"):
                options.append("spoken_lines")
            if hook_type == "at_give":
                options.append("getter")
            if hook_type == "at_told":
                options.append("options")
            if hook_type != "at_told":
                options.append("next_stage")

            # Choose aspect of hook to edit
            inpt = yield f"Select quest hook attribute to edit: ({str(options)})"
            cmd = None
            if inpt.strip() == "":
                self.caller.msg("Cancelled.")
                return
            for cmd_ref in options:
                if cmd_ref.startswith(inpt):
                    cmd = cmd_ref
            if not cmd:
                self.caller.msg("No option found for " + inpt)
                return
            # Set value
            value_set = False
            match cmd:
                case "msg":
                    msg = yield "Enter message:"
                    obj.db.quest_hooks[hook_type][qid][stage]["msg"] = msg
                    value_set = True
                    value = msg

                case "next_stage":
                    stage_input = yield "Enter next stage as QID.Stage:"
                    if valiate_next_stage(stage_input):
                        obj.db.quest_hooks[hook_type][qid][stage]["next_stage"] = stage_input
                        value_set = True
                        value = stage_input

                case "spoken_lines":
                    line_inpt = yield "Write lines separated by '/':"
                    lines = line_inpt.split("/")
                    lines = [line.strip() for line in lines]
                    obj.db.quest_hooks[hook_type][qid][stage]["spoken_lines"] = lines
                    value_set = True
                    value = lines

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
                    except (KeyError, IndexError):
                        opt_dict = {"keywords": [], "spoken_lines": [], "next_stage": None}

                    # Choose attribute of dialogue option to edit
                    inpt = yield "Edit keywords, spoken_lines, or next_stage?:"
                    attr = None
                    for attr_ref in ["keywords", "spoken_lines", "next_stage"]:
                        if attr_ref.startswith(inpt):
                            attr = attr_ref
                    if not attr:
                        self.caller.msg("No option found for " + inpt)
                        return

                    # Set value
                    optval_set = False
                    match attr:
                        case "keywords":
                            keywords = yield "Enter keywords separated by comma:"
                            words = keywords.split(",")
                            words = [word.strip() for word in words]
                            opt_dict["keywords"] = words
                            optval_set = True
                            value = words

                        case "spoken_lines":
                            line_inpt = yield "Write lines separated by '/':"
                            lines = line_inpt.split("/")
                            lines = [line.strip() for line in lines]
                            opt_dict["spoken_lines"] = lines
                            optval_set = True
                            value = lines

                        case "next_stage":
                            stage_input = yield "Enter next stage as QID.Stage:"
                            if valiate_next_stage(stage_input):
                                opt_dict["next_stage"] = stage_input
                                optval_set = True
                                value = stage_input

                        case _:
                            self.caller.msg("No valid option found for " + attr)
                            return
                    if optval_set:
                        self.caller.msg(f"Set {attr} to {value}.")

                    # Save option data for this dialogue option to the quest hook data
                    try:
                        obj.db.quest_hooks[hook_type][qid][stage]["options"][opt_num] = opt_dict
                    except KeyError:
                        obj.db.quest_hooks[hook_type][qid][stage]["options"] = []
                        obj.db.quest_hooks[hook_type][qid][stage]["options"].append(opt_dict)
                    except IndexError:
                        obj.db.quest_hooks[hook_type][qid][stage]["options"].insert(opt_num, opt_dict)

                case _:
                    self.caller.msg("No valid option found for " + inpt)

            if value_set:
                self.caller.msg(f"Set {cmd} to {value}.")


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
        quest_dict = get_quest(qid)
        if quest_dict is None:
            quest_dict = {"desc": "", "stages": {}}
            all_quests()[qid] = quest_dict
        stage_dict = get_stage(qid, stage)
        if stage_dict is None:
            stage_dict = {"desc": ""}

        # Set relevant stage data
        stage_dict["objective_type"] = "kill_counter"
        stage_dict["target_type"] = path_to_type
        stage_dict["kill_num"] = num_to_kill
        stage_dict["next_stage"] = next_stage

        # Reflect changed data in all_quests container
        all_quests()[qid]["stages"][stage] = stage_dict

        self.caller.msg(f"{qid}.{stage} stored in global quest data as kill counter:")
        self.caller.msg(stage_dict)


class QuestBuildCmdSet(CmdSet):
    def at_cmdset_creation(self):
        self.add(CmdQuestEdit)
        self.add(CmdQuestHook)
        self.add(CmdKillCounter)
